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
   if not 'user' in session:
       return redirect('\login')
  
   # get the user from the database
   firstname = 'test'
   lastname = 'M'
   lastLogin = 'now'
   Profiletext = 'blah blah'
  
   return render_template('homepage.html',
       firstname = firstname,
       lastname = lastname,
       lastLogin = lastLogin,
       Profiletext = Profiletext
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
    query = ("SELECT UserId, Password FROM users WHERE email = %s")
    cursor.execute(query, (email,))
    session['userid'] = email
    records = cursor.fetchall()
    
    if records:
        if records[0][1] == password:
            # update the session with the new current user
            session['user'] = {
                'id': records[0][0],
                
                
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

@app.route('/edit-account-setting', methods=['POST'])
def update_user():
    return render_template('edit-account-setting.html')
@app.route('/messages/<message_filter>', methods=['GET'])
def search_messages(message_filter):
    if message_filter not in ("Block","Hood","Friend","Neighbor"):
        return make_response(jsonify({"message": "Invalid Visibility Filter. Valid Values are Block,Hood,Friend,Neighbor.   "}), 404)
    user_email = 'eva@example.com'
    if "email" in session:
        user_email = session['email']
    if not user_email:
        return make_response(jsonify({"message": "User Session cannot be found "}), 404)

    query = "SELECT userid from users WHERE email = %s "
    cursor.execute(query,(user_email,))
    
    result = cursor.fetchone()
    if not result:
        return make_response(jsonify({"message": "User does not exist"}), 404)
    user_id = result[0]
   
    query = """ select m.TextBody,t.ThreadID, t.Subject
            From Thread t
            JOIN Message m on m.ThreadiD = t.ThreadID
            JOIN MessageRecipient mr on mr.MessageID = m.MessageID
            JOIN Users u on u.UserID = mr.RecipientID
            where m.VisibilityType = %s AND u.UserID = %s
            AND mr.isRead = FALSE"""
    cursor.execute(query,(message_filter,user_id,))
    result = cursor.fetchall()
    data = []
    for row in result:
        text, thread, subject = row[0],row[1], row[2]
        r = dict(
            text=text, 
            thread=thread,
            subject=subject
        )
        data.append(r)

    return make_response(jsonify(data),200) 

if __name__ == "__main__":
    app.run(debug=True)