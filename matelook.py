#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

# all the imports
import os
import re
from datetime import datetime
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify
from itsdangerous import URLSafeTimedSerializer


# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    PROFILE_IMG_DIR="profile_img",
    # DATABASE=os.path.join(app.root_path, 'db/small_sqlite.db'),
    DATABASE=os.path.join(app.root_path, 'db/medium_SQLite.db'),
    SECRET_KEY='henry_zhu',
    SECURITY_PASSWORD_SALT='henry_zhu_love_cc',

    USERNAME='admin',
    PASSWORD='default',
    TEMPLATES_AUTO_RELOAD=True,
    DEBUG=True,
    SITE_NAME='Fadebook'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


# Database
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


# common functions
def time_date2txt(cur_time=datetime.utcnow()):
    return cur_time.strftime("%Y-%m-%dT%H:%M:%S+0000")


def handle_message(text):
    text_result = text

    if text == 'null' or text is None:
        return '.'

    text_result = re.sub(r'<', '&lt', text_result)
    text_result = re.sub(r'\\n', '<br>', text_result)

    zids = re.findall(r'z[0-9]{7}', text)
    for zid in zids:
        user = query_db('select * from user where zid = ?',
                        [zid], one=True)
        if user:
            zid_html = '<a target="_blank" href="/user/{}">{}</a>'.format(zid, user['full_name'])
            text_result = re.sub(zid, zid_html, text_result)
        else:
            pass
            # print("user {} does not exist??".format(zid))

    return text_result


def get_post_comment_count(posts):
    posts = [dict(row) for row in posts]
    for post in posts:
        post["message"] = handle_message(post["message"])

        comment = query_db('SELECT count(id) as count FROM COMMENT '
                           'WHERE post_id=? ', [post["post_id"]], one=True)
        post["comment"] = comment

    return posts


def get_user_posts(user_zid):
    user_posts = query_db('''SELECT p.id as post_id, time, message, full_name, u.zid as zid, profile_img
                             FROM POST p JOIN USER u ON u.zid=p.zid
                             WHERE u.zid = ? ORDER BY time DESC''',
                          [user_zid])
    user_posts = get_post_comment_count(user_posts)
    return user_posts


def get_mate_posts(user_zid):
    mate_posts = query_db('SELECT p.id as post_id, time, message, full_name, m.mate_zid as zid, profile_img '
                          'FROM POST p JOIN MATES m ON p.zid = m.mate_zid JOIN USER u ON u.zid=p.zid '
                          'WHERE m.user_zid= ? ORDER BY time DESC',
                          [user_zid])
    mate_posts = get_post_comment_count(mate_posts)
    return mate_posts


def get_refresh_comments(post_id):
    comments = get_post_comments_sub(post_id)
    if len(comments) == 0:
        comments_sum = 'add comment'
    else:
        comments_sum = ' comments' if len(comments) > 1 else ' comment'
        comments_sum = str(len(comments)) + comments_sum

    comments_html = render_template('common/comments.html', comments=comments, post_id=post_id)

    return jsonify(post_id=post_id, comments_html=comments_html, comments_sum=comments_sum)


def add_attr_confirm(mates):
    if g.user:
        user_zid = g.user['zid']
        mates = [dict(row) for row in mates]
        for mate in mates:
            mate_sent = query_db('SELECT confirmed FROM MATES WHERE user_zid = ? AND mate_zid = ?',
                                 [user_zid, mate['zid']], one=True)
            mate_receive = query_db('SELECT confirmed FROM MATES WHERE user_zid = ? AND mate_zid = ?',
                                    [mate['zid'], user_zid], one=True)

            if mate_sent and mate_receive:
                mate['relation'] = 'friend'
            elif mate_receive and mate_receive['confirmed'] == 0:
                mate['relation'] = 'receive'

            elif mate_sent and mate_sent['confirmed'] == 0:
                    mate['relation'] = 'sent'
            else:
                mate['relation'] = 'no_friend'
            # print(mate['zid'], user_zid, mate_q['confirmed'])
    return mates


def get_user(zid=-1, email=''):
    return query_db('SELECT * FROM USER WHERE zid = ? OR email = ?',
                    [zid, email], one=True)


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


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

        return render_template('index.html', posts=posts)
    else:
        return redirect(url_for('login'))


def get_post_comments_sub(post_id):
    comments = query_db('SELECT * FROM COMMENT c JOIN USER u ON c.zid=u.zid '
                        'WHERE post_id=? ORDER BY time', [post_id])
    comments = [dict(row) for row in comments]

    for comment in comments:
        comment["message"] = handle_message(comment["message"])

        replies = query_db('SELECT * FROM REPLY r JOIN USER u ON r.zid=u.zid '
                           'WHERE comment_id=? ORDER BY time', [comment["id"]])
        replies = [dict(row) for row in replies]
        comment["replies"] = replies

        for reply in replies:
            reply["message"] = handle_message(reply["message"])

    return comments


@app.route('/get_comments')
def get_post_comments():
    post_id = request.args.get('post_id')
    m = re.match(r"^post_(\d+)$", post_id)
    if len(m.groups()) == 1:
        post_id = m.group(1)
    else:
        return 'wrong post id given..'

    comments = get_post_comments_sub(post_id)

    return render_template('common/comments.html', comments=comments, post_id=post_id)


@app.route('/user/<user_zid>')
def user_profile(user_zid):
    user_info = query_db('SELECT * FROM USER WHERE zid = ?',
                         [user_zid], one=True)

    ''' get user basic info '''
    user_posts = get_user_posts(user_zid)

    ''' combine mate and user post, get top 10 by time '''
    posts = user_posts
    posts = [dict(row) for row in posts]
    posts = sorted(posts, key=lambda x: x['time'], reverse=True)

    ''' user friends'''
    user_mates = query_db('''
        SELECT * FROM MATES m
        LEFT JOIN USER u ON m.mate_zid = u.zid
        WHERE m.user_zid = ?''', [user_zid])
    user_mates = [dict(row) for row in user_mates]
    user_mates = add_attr_confirm(user_mates)

    # get all the requests to g.user
    request_receive = query_db('''
        SELECT * from (SELECT * FROM MATES WHERE mate_zid=? and confirmed=0) m
        LEFT JOIN USER u on m.user_zid = u.zid''', [user_zid])
    request_receive = [dict(row) for row in request_receive]
    for user in request_receive:
        user['relation'] = 'receive'

    user_mates = request_receive + user_mates

    return render_template('test_users.html',
                           user_info=user_info,
                           posts=posts,
                           users=user_mates)


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


@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    """ sign up"""
    if g.user:
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        if not request.form['zid']:
            error = 'You have to enter a username'
        elif not request.form['email'] or \
                '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password_confirm']:
            error = 'The two passwords do not match'
        elif get_user(zid=request.form['zid']) is not None:
            error = 'The zid is already signed up.'
        elif get_user(email=request.form['email']) is not None:
            error = 'The email is already signed up.'
        else:
            db = get_db()
            db.execute('''insert into user (zid, email, password, full_name, profile_img, confirmed)
                          values (?, ?, ?, ?, ?, ?)''',
                       [request.form['zid'], request.form['email'],
                        request.form['password'], request.form['fullname'],
                        'default.png', 0])

            # serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
            # db.execute('''INSERT INTO USER_TO_CONFIRM VALUES (?, ?)''', [request.form['zid'], serializer])
            db.commit()
            flash('You were successfully registered and can login now')
            session['logged_in'] = request.form['zid']
            return redirect(url_for('index'))
    return render_template('signup.html', error=error)


@app.route('/search', methods=['GET'])
def search():
    """ Searching for a user whose name containing a specified substring.
        Searching for posts containing particular words. """
    suggestion = request.args.get('search')
    if suggestion:
        # print("Searching ", suggestion)
        search_users = query_db('SELECT * FROM USER WHERE full_name LIKE ? OR zid = ? LIMIT 10',
                                ['%{}%'.format(suggestion), suggestion])
        search_users = add_attr_confirm(search_users)

        search_posts = query_db('SELECT * FROM POST WHERE message LIKE ? LIMIT 10', ['%{}%'.format(suggestion)])
    else:
        print("no suggestion")

    return render_template('search_result.html',
                           users=search_users, search_posts=search_posts)


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


@app.route('/new_comment')
def new_comment():
    """Post new comment"""
    if session['logged_in']:
        user_zid = session['logged_in']
        comment = request.args.get('comment')
        post_id = request.args.get('post_id')
        cur_time_txt = time_date2txt()

        db = get_db()
        db.execute('INSERT INTO COMMENT (zid, post_id, time, message) values (?, ?, ?, ?)',
                   [user_zid, post_id, cur_time_txt, comment])
        db.commit()

        return get_refresh_comments(post_id)


@app.route('/delete_comment')
def delete_comment():
    """ Delete a comment"""
    if session['logged_in']:
        user_zid = session['logged_in']
        comment_id = request.args.get('comment_id')

        post = query_db('SELECT * FROM COMMENT WHERE id=?', [comment_id], one=True)
        post_id = post["post_id"]

        db = get_db()
        db.execute('''DELETE FROM REPLY WHERE comment_id = ? ''', [comment_id])
        db.execute('''DELETE FROM COMMENT WHERE id=?''', [comment_id])
        db.commit()

        return get_refresh_comments(post_id)


@app.route('/new_post', methods=['GET', 'POST'])
def new_reply():
    """Post new reply"""
    if session['logged_in']:
        user_zid = session['logged_in']
        reply = request.args.get('reply')
        comment_id = request.args.get('comment_id')
        cur_time_txt = time_date2txt()

        post = query_db('SELECT * FROM COMMENT WHERE id=?', [comment_id], one=True)
        post_id = post["post_id"]

        db = get_db()
        db.execute('INSERT INTO REPLY (zid, comment_id, time, message) values (?, ?, ?, ?)',
                   [user_zid, comment_id, cur_time_txt, reply])
        db.commit()

        return get_refresh_comments(post_id)


@app.route('/delete_reply')
def delete_reply():
    """ Delete a reply"""
    if session['logged_in']:
        reply_id = request.args.get('reply_id')

        reply = query_db('SELECT * FROM REPLY WHERE id=?', [reply_id], one=True)
        comment_id = reply['comment_id']

        comment = query_db('SELECT * FROM COMMENT WHERE id=?', [comment_id], one=True)
        post_id = comment["post_id"]

        db = get_db()
        db.execute('''DELETE FROM REPLY WHERE id = ? ''', [reply_id])
        db.commit()

        return get_refresh_comments(post_id)


@app.route('/delete_post')
def delete_post():
    """ Delete a post"""
    if session['logged_in']:
        post_id = request.args.get('post_id')

        db = get_db()
        result = db.execute('''DELETE FROM POST WHERE id = ? ''', [post_id])
        db.commit()

        return jsonify(return_code=0)


@app.route('/add_friend')
def add_friend():
    """ send add friend request """
    if session['logged_in']:
        mate_zid = request.args.get('zid')
        user_zid = g.user['zid']

        if mate_zid != '' and user_zid != '':
            db = get_db()
            r = query_db('SELECT * FROM MATES WHERE user_zid=? AND mate_zid=?', [user_zid, mate_zid], one=True)

            if not r:
                db.execute('INSERT INTO MATES (user_zid, mate_zid, confirmed) values (?, ?, ?)',
                           [user_zid, mate_zid, 0])
                db.commit()

        return jsonify(return_code=0)


@app.route('/remove_friend')
def remove_friend():
    """ remove a friend """
    if session['logged_in']:
        mate_zid = request.args.get('zid')
        user_zid = g.user['zid']

        if mate_zid != '' and user_zid != '':
            db = get_db()
            r = query_db('SELECT * FROM MATES WHERE (user_zid=? AND mate_zid=?) OR (mate_zid=? AND user_zid=?)',
                         [user_zid, mate_zid, user_zid, mate_zid], one=True)

            if r:
                db.execute('DELETE FROM MATES WHERE mate_zid=? AND user_zid=?',
                           [user_zid, mate_zid])
                db.execute('DELETE FROM MATES WHERE mate_zid=? AND user_zid=?',
                           [mate_zid, user_zid])
                db.commit()

        return jsonify(return_code=0)


@app.route('/accept_friend')
def accept_friend():
    """ accept friend request """
    if session['logged_in']:
        mate_zid = request.args.get('zid')
        user_zid = g.user['zid']

        if mate_zid != '' and user_zid != '':
            db = get_db()
            r = query_db('SELECT * FROM MATES WHERE user_zid=? AND mate_zid=? AND confirmed=0',
                         [mate_zid, user_zid], one=True)

            if r:
                db.execute('UPDATE MATES SET confirmed=1 WHERE user_zid=? AND mate_zid=? AND confirmed=0',
                           [mate_zid, user_zid])
                db.execute('INSERT INTO MATES (user_zid, mate_zid, confirmed) values (?, ?, ?)',
                           [user_zid, mate_zid, 0])
                db.commit()
            else:
                error = 'request does not exit'

        return jsonify(return_code=0, error=error)


if __name__ == '__main__':
    app.run()
