#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import (
    Flask, 
    request, make_response, jsonify, session,
    render_template, url_for, redirect
)
import psycopg2 
from psycopg2 import extras
import bcrypt
import pandas as pd
import datetime
import random
from flask_cors import CORS


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

@app.route('/', methods=['GET'])
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
    pendingfriends_query =  """
            SELECT u.firstname, u.lastname, u.lastlogin
            FROM users u
            JOIN friendship f ON u.userid = f.receiver_id OR u.userid = f.requester_id
            WHERE (f.receiver_id = %s OR f.requester_id = %s) AND f.status = 'Pending'
            AND u.userid != %s;
        """
    #firstname,lastname,lastlogin = friends_data
    cursor.execute(pendingfriends_query, (user_id,user_id,user_id,))
    pendingfriends = cursor.fetchall()
    print(pendingfriends)
    # Close cursor and connection
    cursor.close()

    #lastLogin = 'now'
    #ProfiletText = 'blah blah'
    print("Friends:", friends) 
    # Render the homepage with the fetched data
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
                           pendingFriends=pendingfriends
                           

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
                'zip': records[0][6]
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
 
@app.route('/register', methods=['POST'])
def register_user():
    first_name = request.json['fname']
    last_name = request.json['lname']

    street_addr = request.json['street']
    city = request.json['city']
    state = request.json['state']
    zip_code = int(request.json['zipcode'])

    email = request.json['email']
    password = request.json['password']
    
    

    query = ("select * from users where email = %s")
    cursor.execute(query, (email,))
    
    records = cursor.fetchall()
    neighborhood_center_lat = 35.0
    neighborhood_center_long = -74.0
    lat_range = (neighborhood_center_lat - 0.01, neighborhood_center_lat + 0.01)  # Adjust the range as needed
    long_range = (neighborhood_center_long - 0.01, neighborhood_center_long + 0.01)  # Adjust the range as needed
    home_coords_lat = round(random.uniform(lat_range[0], lat_range[1]), 6)
    home_coords_long = round(random.uniform(long_range[0], long_range[1]), 6)
    last_login = datetime.datetime.now().strftime('%Y-%m-%d')
   
    if (records):
        response = make_response(
            jsonify(
                {"message": "User already exists."}
            ),
            400
        )
        response.headers["Content-Type"] = "application/json"
        return response
    else:
        last_id_query = ("SELECT userid FROM users ORDER BY userid DESC LIMIT 1")
      
        cursor.execute(last_id_query)
        records = cursor.fetchall()
        #HomeCords Lat and log are auto generated
       
        lastest_user_id = records[0][0] 
        query = ("""insert into users (userid, firstname, lastname, streetaddress, city, state, zip,  email, password, blockid, hoodid, homecoordslat, homecoordslong, lastlogin)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s,%s)""")
        try:
            cursor.execute(query, ( lastest_user_id + 1, first_name, last_name, street_addr, city, state, zip_code, email, password,1,1, home_coords_lat, home_coords_long, last_login))
            conn.commit()
            response = make_response(
                jsonify(
                    {
                        "message": "User registered successfully!",
                        "userid": int(records[0]['userid']) + 1,
                        "email": email
                    }
                ),
                201
            )
            response.headers["Content-Type"] = "application/json"
            session['userid'] = email
            return response
        except Exception as e:
            response = make_response(
                jsonify(
                    {"message": f"Error registering user: {str(e)}"}
                ),
                404
            )
            response.headers["Content-Type"] = "application/json"
            return response

@app.route('/timeline', methods=['GET','POST'])
def showTimeline():
    # Check if the user is not logged in and redirect if necessary
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Get the user email from the session to use in queries
    user_id= session['user']['id']

    message_filter = None

    # Prepare a cursor to execute queries
    cursor = conn.cursor()
   
    query = """ 
        SELECT 
            m.TextBody,t.ThreadID, t.Subject
        FROM Thread t
        JOIN Message m on m.ThreadiD = t.ThreadID
        JOIN MessageRecipient mr on mr.MessageID = m.MessageID
        JOIN Users u on u.UserID = mr.RecipientID
        WHERE 
            u.UserID = %s
            AND mr.isRead = FALSE
    """

    values = [user_id]
    if message_filter is not None:
        query += ' AND m.VisibilityType = %s '
        values.append(message_filter)

    cursor.execute(query, values)
    result = cursor.fetchall()
    feed = []
    for row in result:
        text, thread, subject = row[0],row[1], row[2]
        r = dict(text=text, thread=thread, subject=subject)
        feed.append(r)
    return render_template('timeline.html',feed=feed)
        
@app.route('/editAccountSettings', methods=['GET','POST'])
def editSettings():
    # Check if the user is not logged in and redirect if necessary
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Get the user email from the session to use in queries
    user_id= session['user']['id']

    message_filter = None

    # Prepare a cursor to execute queries
    cursor = conn.cursor()
   
    query = """ 
        SELECT 
            m.TextBody,t.ThreadID, t.Subject
        FROM Thread t
        JOIN Message m on m.ThreadiD = t.ThreadID
        JOIN MessageRecipient mr on mr.MessageID = m.MessageID
        JOIN Users u on u.UserID = mr.RecipientID
        WHERE 
            u.UserID = %s
            AND mr.isRead = FALSE
    """

    values = [user_id]
    if message_filter is not None:
        query += ' AND m.VisibilityType = %s '
        values.append(message_filter)

    cursor.execute(query, values)
    result = cursor.fetchall()
    feed = []
    for row in result:
        text, thread, subject = row[0],row[1], row[2]
        r = dict(text=text, thread=thread, subject=subject)
        feed.append(r)
    return render_template('editAccountSettings.html',)

if __name__ == "__main__":
    app.run(debug=True)