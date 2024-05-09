#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import (
    Flask, 
    request, make_response, jsonify, session,
    render_template, url_for, redirect,flash
)
import psycopg2 
from psycopg2 import extras
import bcrypt
import pandas as pd
import datetime
import random
from flask_cors import CORS
from werkzeug.utils import secure_filename


app = Flask(__name__)
cors = CORS(app)

# app.config['CORS_HEADERS'] = 'Content-Type'

# Connect to the database 
conn = psycopg2.connect(database="project", user="postgres", 
                        password="root", host="localhost", port="5432") 
cursor = conn.cursor(cursor_factory=extras.DictCursor)
# Ensure to close cursor and connection properly in actual app logic
conn.commit()


app.config["SECRET_KEY"] = 'some key that you will never guess'

@app.route('/', methods=['GET','POST'])
def home():
    # Check if the user is not logged in and redirect if necessary
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Get the user email from the session to use in queries
    user_email = session['user']['email']  # assuming 'user' in session contains the email
    user_id= session['user']['id']
    # Prepare a cursor to execute queries
    cursor = conn.cursor()

    # Query to fetch user details from Users table
    user_query = """
    SELECT firstname, lastname, lastlogin,email, streetaddress,city,state,zip,userid
    FROM users
    WHERE email = %s
    """
    cursor.execute(user_query, (user_email,))
    user_data = cursor.fetchone()

    # Handling no user data found
    if user_data is None:
        return "User not found", 404

    firstname, lastname, lastLogin, email, streetaddress,city,state, zip, user_id = user_data
     # Query to fetch user profile details
    profile_query = """
    SELECT profiletext,familydetails
    FROM userprofile
    WHERE userid = %s
    """
    cursor.execute(profile_query, (user_id,))
    profile_result = cursor.fetchone()

    # If profile not found, use a default message
    Profiletext = profile_result[0] if profile_result else "No profile available"
    familydetails = profile_result[1] if profile_result else "No profile available"

    #gets friends last login and who you are friends with 
    friends_query =  """
            SELECT u.firstname, u.lastname, u.lastlogin
            FROM users u
            JOIN friendship f ON u.userid = f.receiver_id OR u.userid = f.requester_id
            WHERE (f.receiver_id = %s OR f.requester_id = %s) AND f.status = 'Accepted'
            AND u.userid != %s;
        """
    #firstname,lastname,lastlogin = friends_data
    cursor.execute(friends_query, (user_id,user_id,user_id,))
    friends = cursor.fetchall()
    #gets all the people you are friends with 
    pendingfriends_query =  """
            SELECT u.firstname, u.lastname, u.lastlogin, f.requester_id, f.receiver_id, f.updatedat
                FROM users u
                JOIN friendship f ON u.userid = f.requester_id
                WHERE f.receiver_id = %s AND f.status = 'Pending';
        """
    #firstname,lastname,lastlogin = friends_data
    cursor.execute(pendingfriends_query, (user_id,))
    pendingfriends = cursor.fetchall()
    print(pendingfriends)
    # Close cursor and connection
    all_users_query = """
    SELECT u.firstname, u.lastname, u.lastlogin, u.email, u.streetaddress, u.city, u.state, u.zip, u.userid
    FROM users u
    WHERE u.userid != %s
    AND u.userid NOT IN (
        SELECT f.requester_id FROM friendship f WHERE f.receiver_id = %s
        UNION
        SELECT f.receiver_id FROM friendship f WHERE f.requester_id = %s
    )
    """
    cursor.execute(all_users_query, (user_id, user_id, user_id))
    all_users = cursor.fetchall()


    #lastLogin = 'now'
    #ProfiletText = 'blah blah'
    print("Friends:", friends) 
    print(all_users)
    #FRIEND REQUEST ACCEPT/DECLINE
    if request.method == 'POST':
        action = request.form.get('action', '')
        if action == 'send_request':
            friend_id = request.form.get('friend_id')
            if friend_id:
                send_request_query = """
                INSERT INTO friendship (requester_id, receiver_id, status, createdat)
                VALUES (%s, %s, 'Pending', %s)
                """
                cursor.execute(send_request_query, (user_id, friend_id, datetime.datetime.now()))
                conn.commit()
            else:
                print("No friend selected for the request.")
        else:
            # Handle friend request accept/decline
            requester_id = request.form.get('requester_id', None)
            receiver_id = request.form.get('receiver_id', None)
            response = request.form.get('response', None)

            print(f"Requester ID: {requester_id}, Receiver ID: {receiver_id}, Response: {response}")

            if requester_id and receiver_id and response:
                status = "Accepted" if response == "accepted" else "not accepted"
                date = datetime.datetime.now()
                query = 'UPDATE friendship SET status = %s, updatedat = %s WHERE (requester_id = %s AND receiver_id = %s) OR (requester_id = %s AND receiver_id = %s)'
                cursor.execute(query, (status, date, requester_id, receiver_id, receiver_id, requester_id))
                conn.commit()
                print("Number of rows updated:", cursor.rowcount)
            else:
                print("Error: Missing data for requester_id, receiver_id, or response.")


    cursor.close()
    return render_template('homepage.html',
                           firstname=firstname,
                           lastname=lastname,
                           lastLogin=lastLogin,
                           email=email,
                           Profiletext=Profiletext,
                           familydetails=familydetails,
                           street=streetaddress,
                           city=city,
                           state=state,
                           zip=zip,
                           friends=friends,
                           pendingFriends=pendingfriends,
                           all_users=all_users,
                           user_id=user_id
                           )

@app.route('/login', methods=['GET'])
def login():
    if 'user' in session:
        session.pop('user')
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    return redirect(url_for('login'))

@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    email = request.form['email']
    password = request.form['password']

    # Prepare the cursor and database connection
    cursor = conn.cursor()
    #query = ("SELECT UserId, Password FROM users WHERE email = %s")
    query = ("SELECT * FROM users WHERE email = %s")

    cursor.execute(query, (email,))
    session['userid'] = email
    records = cursor.fetchall()
    
    if records:
        print(records)
        if records[0][8] == password:
            # update the session with the new current user
            session['user'] = {
                'id': records[0][0] ,
                'firstname': records[0][1],
                'lastname': records[0][2],
                'email': records[0][7],
                'streetaddress': records[0][3],
                'city': records[0][4],
                'state': records[0][5],
                'zip': records[0][6],
                'lastlogin':records[0][13]
            }

            # Update last login time and commit
            updateQuery = 'UPDATE users SET lastlogin = %s WHERE userid = %s'
            cursor.execute(updateQuery, (datetime.datetime.now(), records[0][0]))
            conn.commit()
                   
            return redirect(url_for('home'))
        else:
            return redirect(url_for('login')) # 'bad username or password'
    else:
            return redirect(url_for('login')) # 'user not found']
 

@app.route('/timeline', methods=['GET', 'POST'], endpoint='timeline')
def showTimeline():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']['id']
    lastlogin = session['user'].get('lastlogin')
    message_filter = request.args.get('message_filter')

    cursor = conn.cursor()

    # Fetch all users except the current user for DM purposes
    cursor.execute("SELECT UserID, FirstName, LastName FROM Users WHERE UserID != %s", (user_id,))
    all_users = cursor.fetchall()

    if request.method == 'POST':
        message_text = request.form['message_text']
        title = request.form.get('title', '')
        subject = request.form.get('subject', '')
        visibility_type = request.form['visibility_type']
        thread_id = request.form.get('thread_id')
        recipient_id = request.form.get('recipient_id', None)

        current_time = datetime.datetime.now()

        if visibility_type == 'DM' and recipient_id:
            # Insert direct message
            post_message_query = """
            INSERT INTO Message (Title, TextBody, AuthorID, ThreadID, Timestamp, VisibilityType, recipientid) 
            VALUES (%s, %s, %s, NULL, %s, 'DM', %s)
            """
            cursor.execute(post_message_query, (title, message_text, user_id, current_time, recipient_id))
        elif thread_id:
            # Posting to an existing thread
            post_message_query = """
            INSERT INTO Message (Title, TextBody, AuthorID, ThreadID, Timestamp, VisibilityType) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(post_message_query, (title, message_text, user_id, thread_id, current_time, visibility_type))
        else:
            # Starting a new thread
            cursor.execute("SELECT COALESCE(MAX(ThreadID), 0) + 1 FROM Thread;")
            new_thread_id = cursor.fetchone()[0]
            insert_thread_query = "INSERT INTO Thread (ThreadID, Subject) VALUES (%s, %s);"
            cursor.execute(insert_thread_query, (new_thread_id, subject))
            # Insert initial message for new thread
            post_message_query = """
            INSERT INTO Message (Title, TextBody, AuthorID, ThreadID, Timestamp, VisibilityType) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(post_message_query, (title, message_text, user_id, new_thread_id, current_time, visibility_type))

        conn.commit()

    keyword = request.form.get('keyword')

    if keyword:
        search_query = """
        SELECT mr.MessageID, m.Title, m.TextBody, m.Timestamp, u.FirstName, u.LastName
        FROM MessageRecipient mr
        JOIN Message m ON m.MessageID = mr.MessageID
        JOIN Users u ON u.UserID = m.AuthorID
        WHERE mr.recipientID = %s AND (m.TextBody ILIKE %s OR m.Title ILIKE %s)
        """
        params = [user_id, '%' + keyword + '%', '%' + keyword + '%']

        cursor.execute(search_query, tuple(params))
        search_results = cursor.fetchall()

        search_results_data = []
        for row in search_results:
            message_id, title, text, timestamp, author_firstname, author_lastname = row
            search_results_data.append({
                'message_id': message_id,
                'title': title,
                'text': text,
                'timestamp': timestamp.isoformat(),
                'author_firstname': author_firstname,
                'author_lastname': author_lastname
            })

    # Fetch existing threads to populate the form dropdown
    fetch_threads_query = """
    SELECT t.threadid, t.subject 
    FROM Thread t
    JOIN Message m ON m.ThreadID = t.ThreadID
    JOIN MessageRecipient mr ON mr.MessageID = m.MessageID
    WHERE mr.RecipientID = %s
    """
    cursor.execute(fetch_threads_query, (user_id,))
    existing_threads = cursor.fetchall()

    # Fetch direct messages for the user
    direct_messages_query = """
    SELECT m.MessageID, m.Title, m.TextBody, m.Timestamp, u.FirstName, u.LastName
    FROM Message m
    JOIN Users u ON u.UserID = m.AuthorID
    WHERE m.recipientid = %s AND m.VisibilityType = 'DM'
    ORDER BY m.Timestamp DESC
    """
    cursor.execute(direct_messages_query, (user_id,))
    direct_messages = cursor.fetchall()

    if message_filter:
        message_filter = message_filter.title()
        visibility_query = """
        SELECT m.TextBody, t.ThreadID, t.Subject, u2.FirstName AS AuthorFirstName, 
               u2.LastName AS AuthorLastName, m.Timestamp, m.VisibilityType, m.Title
        FROM Thread t
        JOIN Message m ON m.ThreadID = t.ThreadID
        JOIN MessageRecipient mr ON mr.MessageID = m.MessageID
        JOIN Users u ON u.UserID = mr.RecipientID
        JOIN Users u2 ON u2.UserID = m.AuthorID
        WHERE u.UserID = %s AND mr.isRead = FALSE AND m.VisibilityType = %s
        ORDER BY m.Timestamp DESC
        """
        cursor.execute(visibility_query, (user_id, message_filter))
    else:
        recent_query = """
        SELECT m.TextBody, t.ThreadID, t.Subject, u2.FirstName AS AuthorFirstName, 
               u2.LastName AS AuthorLastName, m.Timestamp, m.VisibilityType, m.Title
        FROM Thread t
        JOIN Message m ON m.ThreadID = t.ThreadID
        JOIN MessageRecipient mr ON mr.MessageID = m.MessageID
        JOIN Users u ON u.UserID = mr.RecipientID
        JOIN Users u2 ON u2.UserID = m.AuthorID
        WHERE u.UserID = %s AND mr.isRead = FALSE AND m.Timestamp > %s
        ORDER BY m.Timestamp DESC
        """
        cursor.execute(recent_query, (user_id, lastlogin))

    result = cursor.fetchall()
    visibility_groups = {}
    recent_messages = []

    for row in result:
        text, thread_id, subject, author_first_name, author_last_name, timestamp, visibility_type, title = row
        formatted_timestamp = datetime.datetime.strftime(timestamp, "%Y-%m-%d")
        message = {
            'text': text,
            'title': title,
            'subject': subject,
            'author': f"{author_first_name} {author_last_name}",
            'timestamp': formatted_timestamp
        }

        if visibility_type not in visibility_groups:
            visibility_groups[visibility_type] = {}
        if thread_id not in visibility_groups[visibility_type]:
            visibility_groups[visibility_type][thread_id] = {
                'subject': subject,
                'messages': []
            }
        visibility_groups[visibility_type][thread_id]['messages'].append(message)

        recent_messages.append(message)

    cursor.close()

    return render_template('timeline.html', 
                           existing_threads=existing_threads, 
                           all_users=all_users,  # Ensure this is passed to the template
                           direct_messages=direct_messages, 
                           visibility_groups=visibility_groups, 
                           recent_messages=recent_messages, 
                           firstname=session['user']['firstname'], 
                           lastname=session['user']['lastname'], 
                           lastlogin=lastlogin)

@app.route('/register')
def register():
   return render_template('registration.html')

@app.route('/registerAuth', methods=['GET','POST'])
def registerAuth():
    first_name = request.form['fname']
    last_name = request.form['lname']

    street_addr = request.form['street']
    city = request.form['city']
    state = request.form['state']
    zip_code = int(request.form['zipcode'])

    email = request.form['email']
    password = request.form['password']
    
    

    query = ("select * from users where email = %s")
    cursor.execute(query, (email,))
    
    records = cursor.fetchone()
    neighborhood_center_lat = 35.0
    neighborhood_center_long = -74.0
    lat_range = (neighborhood_center_lat - 0.01, neighborhood_center_lat + 0.01)  # Adjust the range as needed
    long_range = (neighborhood_center_long - 0.01, neighborhood_center_long + 0.01)  # Adjust the range as needed
    home_coords_lat = round(random.uniform(lat_range[0], lat_range[1]), 6)
    home_coords_long = round(random.uniform(long_range[0], long_range[1]), 6)
    last_login = datetime.datetime.now().strftime('%Y-%m-%d')
    error = None
    if records:
         # If the previous query returns data, then user exists
        error = "It seems like this user already exists, try logging in. "
        print('record',records)
        return render_template('login.html', error=error)
    else:
        latest_id_query = ("select userid FROM users ORDER BY userid DESC Limit 1")
        cursor.execute(latest_id_query)
        print('latest id',latest_id_query)
        records = cursor.fetchall()
        #HomeCords Lat and log are auto generated
       
        lastest_user_id = records[0][0] 
        query = ("""insert into users (userid , firstname, lastname, streetaddress, city, state, zip,  email, password, blockid, hoodid, homecoordslat, homecoordslong, lastlogin)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s,%s)""")
        print('latest user',lastest_user_id)
        cursor.execute(query, ( lastest_user_id + 1, first_name, last_name, street_addr, city, state, zip_code, email, password,None,None, home_coords_lat, home_coords_long, last_login))
        conn.commit()
        
        session['email'] = email
        return render_template('homepage.html',error=error)
    


@app.route('/editAccountSettings', methods=['GET','POST'])
def editAccountSettings():
    
    if 'user' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    user_id = session['user']['id']
    print(request.form)  # This will print all form data received

    # Collect form data
    street = request.form.get('streetaddress')
    city = request.form.get('city')
    state = request.form.get('state')
    zipcode = request.form.get('zipcode')
    photo = request.form.get('photo')
    profile_text = request.form.get('profiletext')
    family_details = request.form.get('familydetails')

  
        # Update Users table
    update_user_query = """
        UPDATE users SET streetaddress = %s, city = %s, state = %s, zip = %s
        WHERE userid = %s;
        """
    cursor.execute(update_user_query, (street, city, state, zipcode, user_id))

        # Update UserProfile table
    update_profile_query = """
        UPDATE UserProfile SET ProfileText = %s, PhotoURL = %s, FamilyDetails = %s
        WHERE userid = %s;
        """
    cursor.execute(update_profile_query, (profile_text, photo, family_details, user_id))

    conn.commit()
     
    print("Profile Text:", profile_text)  # Debug print to check data
    print("Family Details:", family_details)   


    return render_template('editAccountSettings.html',firstname=session['user']['firstname'], lastname=session['user']['lastname'])
def showTimelinetest():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']['id']
    lastlogin = session['user']['lastlogin']
    block_id = session['user']['block_id']  # Assuming this is stored in session

    conn = psycopg2.connect("dbname=yourdb user=youruser password=yourpassword")
    cursor = conn.cursor()

    # Existing query for threads and messages
    query_messages = """
        SELECT ...
        FROM Messages
        WHERE conditions
    """
    cursor.execute(query_messages)
    threads = cursor.fetchall()

    # New query for new members
    query_new_members = """
        SELECT u.FirstName, u.LastName, u.Email, u.JoinDate
        FROM Users u
        WHERE u.JoinDate > %s AND u.BlockID = %s
    """
    cursor.execute(query_new_members, (lastlogin, block_id))
    new_members = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('timeline.html', threads=threads, new_members=new_members, firstname=session['user']['firstname'], lastname=session['user']['lastname'], lastlogin=lastlogin.strftime("%Y-%m-%d"))

@app.route('/follow/block', methods=['POST'])
def follow_block():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    block_name = request.form.get('block_name')  # Get block name from request JSON
    
    # Query to retrieve the BlockID based on block name
    block_query = """
    SELECT b.BlockID
    FROM Block b
    WHERE b.BlockName = %s
    """
    cursor.execute(block_query, (block_name,))
    block_id = cursor.fetchone()
    
    if not block_id:
        return "Block not found.", 404
    
    # Check if the user is already following the block
    check_follow_query = """
    SELECT COUNT(*)
    FROM BlockFollowing
    WHERE UserID = %s AND BlockID = %s
    """
    cursor.execute(check_follow_query, (user_id, block_id[0]))
    if cursor.fetchone()[0] > 0:
        return "Already following this block.", 400
    
    # Insert record into BlockFollowing table
    follow_query = """
    INSERT INTO BlockFollowing (UserID, BlockID)
    VALUES (%s, %s)
    """
    cursor.execute(follow_query, (user_id, block_id[0]))
    conn.commit()
    
    return "Successfully followed block.", 201

@app.route('/follow/neighbor', methods=['POST'])
def follow_neighbour():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    first = request.form.get('first_name')  # Get block name from request JSON
    last = request.form.get('last_name') 
    
    # Query to retrieve the BlockID based on block name
    block_query = """
    SELECT UserId
    FROM Users
    WHERE FirstName = %s AND LastName = %s
    """
    cursor.execute(block_query, (first,last))
    block_id = cursor.fetchone()
    
    if not block_id:
        return "User not found.", 404
    
    
    # Check if the user is already following the block
    check_follow_query = """
    SELECT COUNT(*)
    FROM Neighbor
    WHERE (UserId = %s AND NeighborId = %s) OR (UserId = %s AND NeighborId = %s)
    """
    cursor.execute(check_follow_query, (user_id, block_id[0], block_id[0], user_id))
    if cursor.fetchone()[0] > 0:
        return "This person is already your neighbor.", 400
    
    # Insert record into BlockFollowing table
    follow_query = """
    INSERT INTO Neighbor (UserID, NeighborId)
    VALUES (%s, %s)
    """
    cursor.execute(follow_query, (user_id, block_id[0]))
    conn.commit()
    
    return "You have a new neighbour, Yay!.", 201



# @app.route('/search/messages', methods=['POST'])
# def search_messages():
#     # Get keyword from query parameter
#     if 'user' not in session:
#         return redirect(url_for('login'))
    
#     # Get the user email from the session to use in queries
#     user_id= session['user']['id']
#     keyword = request.form.get('keyword')

#     # latitude = request.args.get('latitude')  # Optional: latitude for geographical search
#     # longitude = request.args.get('longitude')  # Optional: longitude for geographical search
    
#     # Perform search based on keyword and/or geographical proximity
#     search_query = """
#     SELECT mr.MessageID, m.Title, m.TextBody, m.Timestamp, u.FirstName, u.LastName
#     FROM MessageRecipient mr
#     JOIN Message m ON m.Messageid = mr.MessageID
#     JOIN Users u on u.UserId = m.authorID
#     WHERE mr.recipientId = %s AND (m.TextBody ILIKE %s OR m.Title ILIKE %s)
#     """
#     params = [user_id, '%' + keyword + '%', '%' + keyword + '%']
    
#     # if latitude and longitude:
#     #     search_query += " AND earth_distance(ll_to_earth(m.Latitude, m.Longitude), ll_to_earth(%s, %s)) < m.Radius"
#     #     params.extend([latitude, longitude])
    
#     cursor.execute(search_query, tuple(params))
#     search_results = cursor.fetchall()
    
#     # Prepare search results data
#     search_results_data = []
#     for row in search_results:
#         message_id, title, text, timestamp, author_firstname, author_lastname = row
#         search_results_data.append({
#             'message_id': message_id,
#             'title': title,
#             'text': text,
#             'timestamp': timestamp.isoformat(),
#             'author_firstname': author_firstname,
#             'author_lastname': author_lastname
#         })
    
#     return render_template('timeline.html', search_results=search_results_data)


if __name__ == '__main__':
    app.run(debug=True)