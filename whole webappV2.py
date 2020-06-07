#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 22:41:16 2020

@author: ATAEI
"""

from flask import (
    Flask, render_template, request, redirect, flash, url_for, session, g
)

from werkzeug.security import check_password_hash, generate_password_hash

from werkzeug.exceptions import abort

from psycopg2 import (
        connect
)

app = Flask(__name__, template_folder="templates")

app.secret_key = b'a1b2c3d4'

@app.route('/signup', methods=('GET', 'POST'))
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        if not username:
            error = 'Please Enter Your Username!'
        elif not password:
            error = 'Please Enter Your Password!'
        else :
            myFile = open('webappConfig.txt')
            connStr = myFile.readline()
            conn = connect(connStr)
            cur = conn.cursor()
            cur.execute(
            'SELECT user_id FROM members WHERE username = %s', (username,))
            if cur.fetchone() is not None:
                error = 'Username  "{}"  already exists, Try another Username!'.format(username)
                cur.close()
                conn.close()

        if error is None:
            cur.execute(
                'INSERT INTO members (username, password) VALUES (%s, %s)',
                (username, generate_password_hash(password))
            )
            cur.close()
            conn.commit()
            conn.close()
            return redirect(url_for('signin'))

        flash(error)

    return render_template('auth/signup.html')

@app.route('/signin', methods=('GET', 'POST'))
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        myFile = open('webappConfig.txt')
        connStr = myFile.readline()
        conn = connect(connStr)
        cur = conn.cursor()
        error = None
        cur.execute(
            'SELECT * FROM members WHERE username = %s', (username,)
        )
        user = cur.fetchone()
        cur.close()
        conn.commit()
        conn.close()

        if user is None:
            error = '"{}" does not exist, Please SignUp!'.format(username)
        elif not check_password_hash(user[2], password):
            error = 'Incorrect password!'

        if error is None:
            session.clear()
            session['user_id'] = user[0]
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/signin.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def load_signedin_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        myFile = open('webappConfig.txt')
        connStr = myFile.readline()
        conn = connect(connStr)
        cur = conn.cursor()
        cur.execute(
            'SELECT * FROM members WHERE user_id = %s', (user_id,)
        )
        g.user = cur.fetchone()
        cur.close()
        conn.commit()
        conn.close()
    if g.user is None:
        return False
    else: 
        return True


@app.route('/')
@app.route('/index')
def index():
    myFile = open('webappConfig.txt')
    connStr = myFile.readline()
    conn = connect(connStr)
    cur = conn.cursor()
    cur.execute(
            """SELECT members.username, data.post_id, data.date, data.latitude, data.longitude, data.litter
               FROM members, data WHERE  
                    members.user_id = data.author_id"""
                    )
    posts = cur.fetchall()
    cur.close()
    conn.commit()
    conn.close()
    load_signedin_user()

    return render_template('blog/index.html', posts=posts)

@app.route('/create', methods=('GET', 'POST'))
def create():
    if load_signedin_user():
        if request.method == 'POST' :
            latitude = request.form['latitude']
            longitude = request.form['longitude']
            litter = request.form['litter']
            error = None
            
            if not litter :
                error = 'Please Enter kind of Litter!'
            if not latitude :
                error = 'Please Enter Latitude!'
            if not longitude :
                error = 'Please Enter Longitude!'
            if error is not None :
                flash(error)
                return redirect(url_for('index'))
            else : 
                    myFile = open('webappConfig.txt')
                    connStr = myFile.readline()
                    conn = connect(connStr)
                    cur = conn.cursor()
                    cur.execute('INSERT INTO data (latitude, longitude, litter, author_id) VALUES (%s, %s, %s, %s)', 
                               (latitude, longitude, litter, g.user[0])
                               )
                    cur.close()
                    conn.commit()
                    conn.close()
                    return redirect(url_for('index'))
        else :
            return render_template('blog/create.html')
    else :
        error = 'Only SignedIn Users Can Add New Cases, Please SignIn!'
        flash(error)
        return redirect(url_for('signin'))
   
def get_post(id):
    myFile = open('webappConfig.txt')
    connStr = myFile.readline()
    conn = connect(connStr)
    cur = conn.cursor()
    cur.execute(
        """SELECT *
           FROM data
           WHERE data.post_id = %s""",
        (id,)
    )
    post = cur.fetchone()

    if post is None:
        abort(404, "Case {} doesn't exist!".format(id))

    if post[1] != g.user[0]:
        abort(403)

    return post

@app.route('/<int:id>/update', methods=('GET', 'POST'))
def update(id):
    if load_signedin_user():
        post = get_post(id)
        if request.method == 'POST' :
            latitude = request.form['latitude']
            longitude = request.form['longitude']
            litter = request.form['litter']
            error = None
            
            if not litter :
                error = 'Please Enter kind of Litter!'
            if not latitude :
                error = 'Please Enter Latitude!'
            if not longitude :
                error = 'Please Enter Longitude!'
            if error is not None :
                flash(error)
                return redirect(url_for('index'))
            else : 
                myFile = open('webappConfig.txt')
                connStr = myFile.readline()
                conn = connect(connStr)
                cur = conn.cursor()
                cur.execute('UPDATE data SET latitude = %s, longitude = %s, litter = %s'
                               'WHERE post_id = %s', 
                               (latitude, longitude, litter, id)
                               )
                cur.close()
                conn.commit()
                conn.close()
                return redirect(url_for('index'))
        else :
            return render_template('blog/update.html', post=post)
    else :
        error = 'Only SignedIn Users Can Update, Please SignIn!'
        flash(error)
        return redirect(url_for('signin'))

@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    myFile = open('webappConfig.txt')
    connStr = myFile.readline()
    conn = connect(connStr)
                
    cur = conn.cursor()
    cur.execute('DELETE FROM data WHERE post_id = %s', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))                               

if __name__ == '__main__':
    app.run(debug=True)
    