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
import datetime

app = Flask(__name__, template_folder="templates")

app.secret_key = b'a1b2c3d4'

def get_dbConn():
    if 'dbConn' not in g:
        myFile = open('webappConfig.txt')
        connStr = myFile.readline()
        g.dbConn = connect(connStr)

    return g.dbConn

def close_dbConn():
    if 'dbConn' in g:
        g.dbComm.close()
        g.pop('dbConn')

@app.route('/signup', methods=('GET', 'POST'))
def signup():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']


        if not username:
            error = 'Please Enter Your Username!'
        elif not password:
            error = 'Please Enter Your Password!'
        else :
            conn = get_dbConn()
            cur = conn.cursor()
            cur.execute(
            'SELECT user_id FROM members WHERE username = %s', (username,))
            if cur.fetchone() is not None:
                error = 'Username  "{}"  already exists, Try another Username!'.format(username)
                cur.close()
                conn.close()

        if error is None:
            conn = get_dbConn()
            cur = conn.cursor()
            password =generate_password_hash(password)

            cur.execute(
                'INSERT INTO members (username, password) VALUES (%s, %s) RETURNING user_id',
                (username, password)
            )
            last_row_id = cur.fetchone()[0]
            cur.close()
            conn.commit()
            session.clear()
            session['user_id'] = last_row_id
            return redirect(url_for('index'))


    return render_template('auth/signup.html',error=error,active='signin')

@app.route('/signin', methods=('GET', 'POST'))
def signin():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_dbConn()
        cur = conn.cursor()
        cur.execute(
            'SELECT * FROM members WHERE username = %s', (username,)
        )
        user = cur.fetchone()
        cur.close()
        conn.commit()

        if user is None:
            error = '"{}" does not exist, Please SignUp!'.format(username)

        elif not check_password_hash(user[2], password):
            error = "Wrong password"

        if error is None:
            session.clear()
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        else:
            return render_template('auth/signin.html',error=error,active='signin')


    return render_template('auth/signin.html',error=error,active="signin")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def load_signedin_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        conn = get_dbConn()
        cur = conn.cursor()
        cur.execute(
            'SELECT * FROM members WHERE user_id = %s', (user_id,)
        )
        g.user = cur.fetchone()
        cur.close()
        conn.commit()
    if g.user is None:
        return False
    else:
        return True


@app.route('/')
@app.route('/index')
def index():
    conn = get_dbConn()
    cur = conn.cursor()
    cur.execute(
            """SELECT members.username, data.post_id, data.date, data.latitude, data.longitude, data.litter
               FROM members inner join data on members.user_id = data.author_id """
                    )
    datas = cur.fetchall()
    cur.close()
    conn.commit()
    load_signedin_user()

    posts = []

    for post in datas:
        lst = list(post)
        lst[2] =post[2].strftime("%Y/%m/%d")
        posts.append(lst)

    print('data')
    print(g.user)

    return render_template('blog/index.html',active="home",posts=posts)

@app.route('/about')
def about():
    load_signedin_user()
    return render_template('blog/about.html',active="about")

@app.route('/contact')
def contact():
    load_signedin_user()
    return render_template('blog/contact.html',active="contact")



@app.route('/create', methods=('GET', 'POST'))
def create():
    error = None
    if load_signedin_user():
        if request.method == 'POST' :

            latitude = request.form['latitude']

            longitude = request.form['longitude']
            print(request.form)
            litter = request.form['litter']
            print('okok12')
            if not litter :
                error = 'Please Enter kind of Litter!'
            if not latitude :
                error = 'Please Enter Latitude!'
            if not longitude :
                error = 'Please Enter Longitude!'
            if error is not None :
                return render_template('blog/create.html',error=error,active='create')
            else :
                conn = get_dbConn()
                cur = conn.cursor()
                cur.execute('INSERT INTO data (latitude, longitude, litter, author_id) VALUES (%s, %s, %s, %s)',
                            (latitude, longitude, litter, g.user[0])
                            )
                cur.close()
                conn.commit()
                return redirect(url_for('index'))
        else :
            return render_template('blog/create.html',error=error,active='create')
    else :
        error = 'Only SignedIn Users Can Add New Cases, Please SignIn!'
        return render_template('auth/signin.html',error=error)

@app.route('/graph', methods=['GET'])
def graph():
    load_signedin_user()
    conn = get_dbConn()
    cur = conn.cursor()
    cur.execute(
        """SELECT count(1) as count,litter
           FROM data
           GROUP BY litter""",
    )

    datas = cur.fetchall()
    cur.close()

    labels = []
    values = []

    for row in datas:
        labels.append(row[1])
        values.append(row[0])

    max_value = max(values) + 10;

    return render_template('blog/chart.html',labels=labels,values=values,max=max_value,active='graph')


def get_post(id):

    conn = get_dbConn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM data WHERE data.post_id = %s',([id])
    )
    post = cur.fetchone()
    cur.close()
    if post is None:
        abort(404, "Case {0} doesn't exist!".format(id))

    if post[1] != g.user[0]:
        abort(403, "You dont Have permission!!")

    return post

@app.route('/update/<int:id>', methods=('GET', 'POST'))
def update(id):
    error = None
    if load_signedin_user():
        post = get_post(id)
        if request.method == 'POST' :
            latitude = request.form['latitude']
            longitude = request.form['longitude']
            litter = request.form['litter']

            if not litter :
                error = 'Please Enter kind of Litter!'
            if not latitude :
                error = 'Please Enter Latitude!'
            if not longitude :
                error = 'Please Enter Longitude!'
            if error is not None :
                return render_template('blog/update.html', data=post,error=error)
            else :
                conn = get_dbConn()
                cur = conn.cursor()
                cur.execute('UPDATE data SET latitude = %s, longitude = %s, litter = %s'
                               'WHERE post_id = %s',
                               (latitude, longitude, litter, id)
                               )
                cur.close()
                conn.commit()
                return redirect(url_for('index'))
        else :
            return render_template('blog/update.html', data=post,error=error)
    else :
        error = 'Only SignedIn Users Can Update, Please SignIn!'
        return render_template('auth/signin.html',error=error,active="signin")

@app.route('/delete/<int:id>', methods=['GET'])
def delete(id):
    if load_signedin_user():
        get_post(id)
        conn = get_dbConn()
        cur = conn.cursor()
        cur.execute('DELETE FROM data WHERE post_id = %s', (id,))
        conn.commit()
        return redirect(url_for('index'))
    else:
        abort(403, "You dont Have permission!!")

if __name__ == '__main__':
    app.run(debug=True)
