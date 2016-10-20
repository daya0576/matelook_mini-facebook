#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

# all the imports
import os, re
from datetime import datetime
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    PROFILE_IMG_DIR="profile_img",
    # DATABASE=os.path.join(app.root_path, 'db/small_sqlite.db'),
    DATABASE=os.path.join(app.root_path, 'db/large_sqlite.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    TEMPLATES_AUTO_RELOAD=True,
    DEBUG=True
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def time_date2txt(cur_time=datetime.utcnow()):
    return cur_time.strftime("%Y-%m-%dT%H:%M:%S+0000")


def add_zid_link(text):
    text_result = text
    zids = re.findall(r'z[0-9]{7}', text)
    for zid in zids:
        user = query_db('select * from user where zid = ?',
                        [zid], one=True)
        if user:
            zid_html = '<a target="_blank" href="/user/{}">{}</a>'.format(zid, user['full_name'])
            text_result = re.sub(zid, zid_html, text_result)
            text_result = re.sub(r'\\n', '<br>', text_result)
        else:
            pass
            # print("user {} does not exist??".format(zid))

    return text_result


def get_user_posts(user_zid):
    user_posts = query_db('SELECT p.id as post_id, time, message, full_name, u.zid as zid, profile_img '
                          'FROM POST p JOIN USER u ON u.zid=p.zid WHERE u.zid = ? ORDER BY time DESC',
                          [user_zid])
    return user_posts


def get_mate_posts(user_zid):
    mate_posts = query_db('SELECT p.id as post_id, time, message, full_name, m.mate_zid as zid, profile_img '
                          'FROM POST p JOIN MATES m ON p.zid = m.mate_zid JOIN USER u ON u.zid=p.zid '
                          'WHERE m.user_zid= ? ORDER BY time DESC',
                          [user_zid])
    return mate_posts


@app.before_request
def before_request():
    g.user = None
    if 'logged_in' in session:
        g.user = query_db('select * from user where zid = ?',
                          [session['logged_in']], one=True)


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def index():
    if 'logged_in' in session:
        user_zid = session['logged_in']
        mate_posts = get_mate_posts(user_zid)
        user_posts = get_user_posts(user_zid)

        ''' combine mate and user post, get top 10 by time '''
        posts = user_posts+mate_posts
        posts = [dict(row) for row in posts]

        posts = sorted(posts, key=lambda x: x['time'], reverse=True)
        posts = posts[:10]

        for post in posts:
            comments = query_db('SELECT * FROM COMMENT c JOIN USER u ON c.zid=u.zid '
                                'WHERE post_id=? ORDER BY time', [post["post_id"]])
            comments = [dict(row) for row in comments]
            post["comments"] = comments

            for comment in comments:
                comment["message"] = add_zid_link(comment["message"])
                replies = query_db('SELECT * FROM REPLY r JOIN USER u ON r.zid=u.zid '
                                   'WHERE comment_id=? ORDER BY time', [comment["id"]])
                replies = [dict(row) for row in replies]
                comment["replies"] = replies

                for reply in replies:
                    reply["message"] = add_zid_link(reply["message"])

        return render_template('index.html', posts=posts)
    else:
        return render_template('index.html')


@app.route('/user/<user_zid>')
def user_profile(user_zid):
    user_info = query_db('SELECT * FROM USER WHERE zid = ?',
                         [user_zid], one=True)

    user_posts = get_user_posts(user_zid)

    user_mates = query_db('SELECT * FROM MATES m '
                          'LEFT JOIN USER u ON m.mate_zid = u.zid '
                          'WHERE m.user_zid = ?', [user_zid])

    return render_template('test_users.html',
                           user_info=user_info,
                           user_posts=user_posts,
                           user_mates=user_mates)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in."""
    if g.user:
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        zid = request.form['zid']
        password = request.form['password']

        user = query_db('SELECT * FROM USER WHERE zid = ?',
                        [zid], one=True)

        if user is None:
            error = 'Invalid username'
        elif user['password'] != password:
            error = 'Invalid password'
        else:
            flash('You were logged in')
            session['logged_in'] = user['zid']
            return redirect(url_for('index'))

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('logged_in', None)
    return redirect(url_for('index'))


@app.route('/search', methods=['GET'])
def search():
    """ Searching for a user whose name containing a specified substring.
        Searching for posts containing particular words. """
    suggestion = request.args.get('search')
    if suggestion:
        # print("Searching ", suggestion)
        search_users = query_db('SELECT * FROM USER WHERE full_name LIKE "%' + suggestion + '%"')
        search_posts = query_db('SELECT * FROM POST WHERE message LIKE "%' + suggestion + '%"')
    else:
        print("no suggestion")

    return render_template('search_result.html',
                           search_users=search_users, search_posts=search_posts)


@app.route('/post', methods=['GET', 'POST'])
def post():
    """Post new message"""
    if session['logged_in'] and request.method == 'POST'\
            and request.form['message'] != '' and request.form['message'] is not None:
        user_zid = session['logged_in']
        post_message = request.form['message']
        # print('post_message: "{}"'.format(post_message))
        cur_time_txt = time_date2txt()

        db = get_db()
        db.execute('INSERT INTO POST (zid, time, message) values (?, ?, ?)',
                   [user_zid, cur_time_txt, post_message])
        db.commit()

    return redirect(url_for('index'))

# if __name__ == '__main__':
#     app.run()
