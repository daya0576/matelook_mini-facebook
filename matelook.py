#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

# all the imports
import os
import re
from datetime import datetime, timezone
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify

from itsdangerous import URLSafeTimedSerializer
from werkzeug.utils import secure_filename
from functools import wraps

import keys
# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from itsdangerous import URLSafeTimedSerializer
from collections import Counter

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'daya0576@gmail.com'
EMAIL_HOST_PASSWORD = keys.G_EMAIL_KEY
EMAIL_PORT = 587
# EMAIL_PORT = 25
EMAIL_USE_TLS = True

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
# DB_TYPE = 'small'
DB_TYPE = 'medium'
# DB_TYPE = 'large'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/'

# Load default config and override config from an environment variable
app.config.update(dict(
    PROFILE_IMG_DIR="profile_img",
    DATABASE=os.path.join(app.root_path, 'db/{}_SQLite.db'.format(DB_TYPE)),
    SECRET_KEY='henry_zhu',
    SECURITY_PASSWORD_SALT='henry_zhu_love_cc',

    USERNAME='admin',
    PASSWORD='default',
    TEMPLATES_AUTO_RELOAD=True,
    DEBUG=True,
    SITE_NAME='Spring',
    # SERVER_NAME='(Do not forget to confige)'
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


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# common functions
def time_date2txt(cur_time=None):
    if cur_time is None:
        cur_time = datetime.now(timezone.utc)

    cur_time_text = cur_time.strftime("%Y-%m-%dT%H:%M:%S%z")

    return cur_time_text


def time_txt2date(time_text):
    date_object = datetime.strptime(time_text, "%Y-%m-%dT%H:%M:%S%z")
    return date_object


def show_time(time):
    time_show = ''
    date_record = time_txt2date(time)
    date_now = datetime.now()

    sub_s = int(date_now.timestamp()-date_record.timestamp())

    if sub_s < 60:
        time_show = 'Just now'
    elif sub_s/60 < 60:
        time_show = '{} MINUTES AGO'.format(sub_s//60)
    elif sub_s/60/60 < 24:
        hours = sub_s // 60 // 60
        time_show = '{} HOURS AGO'.format(hours) if hours != 1 else '{} HOUR AGO'.format(hours)
    elif sub_s/60/60/24 >= 1:
        day = int(sub_s/60/60/24)
        if day == 1:
            time_show = 'YESTERDAY'
        else:
            time_show = '{} days ago'.format(day)

    return time_show


def handle_message(text):
    text_result = text

    if text == 'null' or text is None:
        return '.'

    text_result = re.sub(r'<', '&lt', text_result)
    text_result = re.sub(r'\\n', '<br>', text_result)

    zids = re.findall(r'z[0-9]{7}', text)
    for zid in zids:
        user = get_user(zid=zid)
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
    user_posts = query_db('''SELECT p.id as post_id, time, message, privacy, full_name, u.zid as zid, profile_img
                             FROM POST p JOIN USER u ON u.zid=p.zid
                             WHERE u.zid = ? ORDER BY time DESC''',
                          [user_zid])
    user_posts = get_post_comment_count(user_posts)
    return user_posts


def get_mate_posts(user_zid, cond=''):
    mate_posts = query_db('SELECT p.id as post_id, time, message, privacy, full_name, m.mate_zid as zid, profile_img '
                          'FROM POST p JOIN MATES m ON p.zid = m.mate_zid JOIN USER u ON u.zid=p.zid '
                          'WHERE m.user_zid= ? {} ORDER BY time DESC'.format(cond),
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
    if g.user and mates is not None:
        user_zid = g.user['zid']
        mates = [dict(row) for row in mates]
        for mate in mates:
            mate_sent = query_db('SELECT confirmed FROM MATES WHERE user_zid = ? AND mate_zid = ?',
                                 [user_zid, mate['zid']], one=True)
            mate_receive = query_db('SELECT confirmed FROM MATES WHERE user_zid = ? AND mate_zid = ?',
                                    [mate['zid'], user_zid], one=True)

            if (mate_sent and mate_sent['confirmed'] == 1) \
                    and (mate_receive and mate_receive['confirmed'] == 1):
                mate['relation'] = 'friend'
            elif mate_receive and mate_receive['confirmed'] == 0:
                mate['relation'] = 'receive'

            elif mate_sent and mate_sent['confirmed'] == 0:
                    mate['relation'] = 'sent'
            else:
                mate['relation'] = 'no_friend'
            # print(mate['zid'], user_zid, mate_q['confirmed'])
    return mates


def get_user(zid=-1, email='-1'):
    user = query_db('SELECT * FROM USER WHERE zid = ? OR email = ?',
                    [zid, email], one=True)
    if user:
        user = dict(user)
        if user['profile_img'] == '':
            user['profile_img'] = 'default.png'

        return user
    else:
        return None


def get_user_suspend(zid=-1, email='-1'):
    user = query_db('SELECT * FROM USER_SUSPEND WHERE zid = ? OR email = ?',
                    [zid, email], one=True)
    if user:
        user = dict(user)
        if user['profile_img'] == '':
            user['profile_img'] = 'default.png'

        return user
    else:
        return None


def get_user_to_confirm(zid=-1):
    return query_db('SELECT * FROM USER_TO_CONFIRM WHERE zid = ?', [zid], one=True)


def get_all_mates(zid):
    mates = query_db('''SELECT * FROM MATES m JOIN USER u ON u.zid = m.mate_zid WHERE m.user_zid = ? ''',
                     [zid])
    mates = [dict(row) for row in mates]
    return mates


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def send_email(toaddr, subject, body):
    fromaddr = EMAIL_HOST_USER

    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    # msg['Subject'] = "Follow the link to activate your account."
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    server.starttls()
    server.login(fromaddr, EMAIL_HOST_PASSWORD)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()


@app.before_request
def before_request():
    g.user = None
    if 'logged_in' in session:
        g.user = query_db('select * from user where zid = ?',
                          [session['logged_in']], one=True)
        if not g.user:
            g.user = query_db('select * from USER_SUSPEND where zid = ?',
                              [session['logged_in']], one=True)


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    db = getattr(g, 'sqlite_db', None)
    if db is not None:
        # print("close db....")
        db.close()


@app.route('/')
def index():
    if 'logged_in' in session:
        user_zid = session['logged_in']
        mate_posts = get_mate_posts(user_zid, "AND p.privacy != 'onlyme'")
        user_posts = get_user_posts(user_zid)

        ''' combine mate and user post, get top 10 by time '''
        posts = user_posts+mate_posts
        posts = [dict(row) for row in posts]

        posts = sorted(posts, key=lambda x: x['time'], reverse=True)
        posts = posts[:10]

        for post in posts:
            post['time_show'] = show_time(post['time'])

        return render_template('index.html',
                               posts=posts,
                               load_more_from='index',
                               new_post_error=request.args.get('new_post_error'))
    else:
        return redirect(url_for('login'))


@app.route('/load_more_index')
@login_required
def load_more_index():
    if request.args.get('post_id_start'):
        post_id_start = int(request.args.get('post_id_start'))
        # print("post_id_start", post_id_start)

        user_zid = g.user['zid']
        mate_posts = get_mate_posts(user_zid)
        user_posts = get_user_posts(user_zid)

        ''' combine mate and user post, get top 10 by time '''
        posts = user_posts + mate_posts
        posts = [dict(row) for row in posts]

        posts = sorted(posts, key=lambda x: x['time'], reverse=True)
        posts = posts[post_id_start:post_id_start + 10]

        pos_next_start = -1 if len(posts) < 10 else post_id_start + 10

        # print("pos_next_start", pos_next_start)
        for post in posts:
            post['time_show'] = show_time(post['time'])

        return render_template('common/posts.html', posts=posts, pos_next_start=pos_next_start)


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
@login_required
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
    user_info = get_user(zid=user_zid)
    posts = user_mates = sugg_final = None
    if user_info:
        status = 'owner' if g.user['zid'] == user_zid else 'other'

        ''' get user basic info '''
        user_posts = get_user_posts(user_zid)

        ''' get user posts '''
        posts = user_posts
        posts = [dict(row) for row in posts]
        posts = sorted(posts, key=lambda x: x['time'], reverse=True)
        '''format time'''
        for post in posts:
            post['time_show'] = show_time(post['time'])

        ''' user friends'''
        user_mates = query_db('''
            SELECT * FROM MATES m
            LEFT JOIN USER u ON m.mate_zid = u.zid
            WHERE m.user_zid = ?''', [user_zid])
        if user_mates:
            user_mates = add_attr_confirm(user_mates)

        ''' friends suggestion '''
        a = datetime.now()
        # get all mates of mates
        mates_of_mates = []
        for mate in user_mates:
            mates_of_mate = query_db('''
                        SELECT * FROM MATES m
                        LEFT JOIN USER u ON m.mate_zid = u.zid
                        WHERE m.user_zid = ?''', [mate['zid']])
            mates_of_mate = [dict(row) for row in mates_of_mate]
            # mates_of_mate_zid = [mate_of_mate['zid'] for mate_of_mate in mates_of_mate]
            mates_of_mates += mates_of_mate
        b = datetime.now()

        # count frequency all mates of mates
        c = Counter([mate_of_mate['zid'] for mate_of_mate in mates_of_mates])
        print(c.most_common())

        # save all mates of mates value to dict
        dict_mates_of_mates = {}
        for mate_of_mate in mates_of_mates:
            dict_mates_of_mates[mate_of_mate['zid']] = dict(mate_of_mate)
        # print(dict_mates_of_mates.keys())
        # print(dict_mates_of_mates.values())

        # get final mates zids and filter user and existing friends
        print("friends: ", [mate['zid'] for mate in user_mates])
        sugg_final_zid = []
        for m in c.most_common():
            if m[0] != user_zid and m[0] not in [mate['zid'] for mate in user_mates]:
                sugg_final_zid.append(m)
        print(sugg_final_zid)

        # get final values of suggestion friends,
        sugg_final = []
        for m in sugg_final_zid[:10]:
            mate = dict_mates_of_mates[m[0]]
            mate['common_f'] = m[1]
            sugg_final.append(mate)

        sugg_final = add_attr_confirm(sugg_final)

        # get all the requests to g.user
        request_receive = query_db('''
                    SELECT * from (SELECT * FROM MATES WHERE mate_zid=? and confirmed=0) m
                    LEFT JOIN USER u on m.user_zid = u.zid''', [user_zid])
        request_receive = [dict(row) for row in request_receive]
        for user in request_receive:
            user['relation'] = 'receive'

        user_mates = request_receive + user_mates
    else:
        user_info = get_user_suspend(zid=user_zid)
        if user_info and user_zid == g.user['zid']:
            status = 'suspend'
        else:
            status = 'none'

    return render_template('test_users.html',
                           user_info=user_info, posts=posts, users=user_mates,
                           pos_next_start=-1, status=status, users_suggestion=sugg_final)


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
            user = query_db('SELECT * FROM USER_SUSPEND WHERE zid = ?',
                            [zid], one=True)

        if user is None:
            error = 'Invalid username'
        elif user['password'] != password:
            error = 'Invalid password'
        else:
            # flash('You were logged in')
            session['logged_in'] = user['zid']
            return redirect(url_for('index'))

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    """Logs the user out."""
    # flash('You were logged out')
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
        elif get_user(zid=request.form['zid']) is not None \
                        or get_user_to_confirm(zid=request.form['zid']):
            error = 'The zid is already signed up.'
        elif get_user(email=request.form['email']) is not None:
            error = 'The email is already signed up.'
        else:
            # db = get_db()
            # email = request.form['email']
            # confirmation_key = str(generate_confirmation_token(email))
            #
            # db.execute('''INSERT INTO USER_TO_CONFIRM (zid, email, password, full_name, profile_img, confirmed)
            #               VALUES (?, ?, ?, ?, ?, ?)''',
            #            [request.form['zid'], email,
            #             request.form['password'], request.form['fullname'],
            #             'default.png', confirmation_key])
            #
            # email_subj = 'Follow the link to complete your account creation.'
            # path = url_for('sign_up_confirmation', zid=request.form['zid'], confirmation_key=confirmation_key)
            # root = request.url_root
            # if root and path \
            #         and len(root)>0 and len(path)>0  \
            #         and root[-1] == '/' and path[0] == '/':
            #     root = root[:-1]
            # email_body = 'Here is the link: <a href="{0}">{0}</a>'.format(root+path)
            # send_email(email, email_subj, email_body)
            #
            # db.commit()
            # error = 'Click the link in your email to complete account creation.'

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
            return redirect(url_for('user_profile', user_zid=request.form['zid']))

    return render_template('signup.html', error=error)


@app.route('/sign_up/<zid>/<confirmation_key>', methods=['GET'])
def sign_up_confirmation(zid, confirmation_key):
    user = get_user_to_confirm(zid)
    user_zid = zid
    if user['confirmed'] == confirmation_key:
        session['logged_in'] = zid
        db = get_db()

        if get_user(zid=user_zid):
            db.execute('''DELETE FROM USER WHERE zid = ?''', [user_zid])

        db.execute('''INSERT INTO USER
                          SELECT * FROM USER_TO_CONFIRM WHERE zid = ?''',
                   [user_zid])
        db.execute('''DELETE FROM USER_TO_CONFIRM WHERE zid = ?''', [user_zid])

        db.commit()

        session['logged_in'] = user_zid

        return redirect(url_for('user_profile', user_zid=zid))
    else:
        return render_template('signup.html', error='Do not try to activate other\'s account.')


@app.route('/search', methods=['GET'])
def search():
    """ Searching for a user whose name containing a specified substring.
        Searching for posts containing particular words. """
    suggestion = request.args.get('suggestion')
    if suggestion:
        # print("Searching ", suggestion)
        search_users = query_db('SELECT * FROM USER WHERE full_name LIKE ? OR zid = ? LIMIT 10',
                                ['%{}%'.format(suggestion), suggestion])
        search_users = add_attr_confirm(search_users)

        ''' searching post '''
        search_posts = query_db('''SELECT * FROM POST p
                                   LEFT JOIN USER u ON p.zid=u.zid WHERE message LIKE ? LIMIT 20''',
                                ['%{}%'.format(suggestion)])
        search_posts = [dict(row) for row in search_posts]

        ''' filter posts based on privacy '''
        # all mates of user.
        mates_zid = []
        if session.get('logged_in'):
            mates_zid = [mate['mate_zid'] for mate in get_all_mates(session['logged_in'])]

        filtered_search_posts = []
        for post in search_posts:
            post['post_id'] = post['id']
            if post['privacy'] == 'public':
                filtered_search_posts.append(post)
            elif session.get('logged_in'):
                if post['zid'] in mates_zid and post['privacy'] == 'friends':
                    filtered_search_posts.append(post)
                elif post['zid'] == session['logged_in']:
                    filtered_search_posts.append(post)

        filtered_search_posts = sorted(filtered_search_posts, key=lambda x: x['time'], reverse=True)

        filtered_search_posts = get_post_comment_count(filtered_search_posts)

        for post in filtered_search_posts:
            post['message'] = post['message'].replace(suggestion, "<strong>{}</strong>".format(suggestion))

        '''format time'''
        for post in filtered_search_posts:
            post['time_show'] = show_time(post['time'])

        return render_template('search_result.html',
                               users=search_users, posts=filtered_search_posts, pos_next_start=-1)

    else:
        # print("no suggestion")
        return


@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    """Post new message"""
    error = None
    if request.method == 'POST'\
            and request.form['message'] != '' and request.form['message'] is not None:
        user_zid = session['logged_in']
        post_message = request.form['message']
        post_privacy = request.form['post_privacy']
        # print('post_privacy: "{}"'.format(post_privacy))
        cur_time_txt = time_date2txt()

        db = get_db()
        db.execute('INSERT INTO POST (zid, time, message, privacy) values (?, ?, ?, ?)',
                   [user_zid, cur_time_txt, post_message, post_privacy])
        db.commit()
    elif request.form['message'] == '' or request.form['message'] is None:
        error = "Post cannot be empty"

    return redirect(url_for('index', new_post_error=error))


@app.route('/new_comment')
@login_required
def new_comment():
    """Post new comment"""
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
@login_required
def delete_comment():
    """ Delete a comment"""
    comment_id = request.args.get('comment_id')

    post = query_db('SELECT * FROM COMMENT WHERE id=?', [comment_id], one=True)
    post_id = post["post_id"]

    db = get_db()
    db.execute('''DELETE FROM REPLY WHERE comment_id = ? ''', [comment_id])
    db.execute('''DELETE FROM COMMENT WHERE id=?''', [comment_id])
    db.commit()

    return get_refresh_comments(post_id)


@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_reply():
    """Post new reply"""
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
@login_required
def delete_reply():
    """ Delete a reply"""
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
@login_required
def delete_post():
    """ Delete a post"""
    post_id = request.args.get('post_id')

    db = get_db()
    result = db.execute('''DELETE FROM POST WHERE id = ? ''', [post_id])
    db.commit()

    return jsonify(return_code=0)


@app.route('/add_friend')
@login_required
def add_friend():
    """ send add friend request """
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
@login_required
def remove_friend():
    """ remove a friend """
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
@login_required
def accept_friend():
    """ accept friend request """
    error = ''
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
                       [user_zid, mate_zid, 1])
            db.commit()
        else:
            error = 'request does not exit'

    return jsonify(return_code=0, error=error)


def check_input(text):
    return "" if text is None else text


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/user/<user_zid>/edit', methods=['GET', 'POST'])
@login_required
def user_edit_profile(user_zid):
    user = get_user(zid=user_zid)
    if request.method == 'POST' and user.zid == g.user['zid']:
        full_name = check_input(request.form['full_name'])
        email = check_input(request.form['email'])

        birthday = check_input(request.form['birthday'])
        if len(birthday) == 10:
            birthday = birthday
            # birthday = birthday.replace('-', '/')
            # birthday = "{}/{}/{}".format(birthday[6:], birthday[3:5], birthday[0:2])
        else:
            birthday = user['birthday']

        home_suburb = check_input(request.form['home_suburb'])
        program = check_input(request.form['program'])

        profile_text = check_input(request.form['profile_text'])

        file = None
        # print(request.files)
        if 'profile_img' not in request.files:
            # flash('No file part')
            # profile_img = user['profile_img']
            # print('filename:', 'shit')
            pass
        else:
            file = request.files['profile_img']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            db_img_path = 'dataset-{}/{}/'.format(DB_TYPE, user['zid'])

            st_img_path = 'static/user/{}/{}'.format(app.config['PROFILE_IMG_DIR'], db_img_path)
            st_img_path = os.path.join(st_img_path, 'profile.jpg')
            abs_st_img_path = os.path.abspath(st_img_path)
            # print(abs_st_img_path)

            # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file.save(abs_st_img_path)

            profile_img = os.path.join(db_img_path, 'profile.jpg')
        else:
            profile_img = user['profile_img']

        db = get_db()
        db.execute('''UPDATE USER SET full_name=?, email=?, birthday=?, home_suburb=?, program=?,
                      profile_text=?, profile_img=?
                      WHERE zid=? ''',
                   [full_name, email, birthday, home_suburb, program,
                    profile_text, profile_img, user_zid])

        db.commit()

        return redirect(url_for('user_profile', user_zid=user_zid))
    else:
        return render_template('profile_edit.html', user=user)


@app.route('/user/delete_account')
@login_required
def delete_account():
    user_zid = g.user['zid']

    db = get_db()
    db.execute('''DELETE FROM REPLY WHERE zid = ?''', [user_zid])
    db.execute('''DELETE FROM COMMENT WHERE zid = ?''', [user_zid])
    db.execute('''DELETE FROM POST WHERE zid = ?''', [user_zid])

    db.execute('''DELETE FROM ENROLLMENT WHERE zid = ?''', [user_zid])
    db.execute('''DELETE FROM MATES WHERE user_zid = ? OR mate_zid = ?''', [user_zid, user_zid])

    db.execute('''DELETE FROM USER WHERE zid = ? ''', [user_zid])

    db.commit()
    # print("success")

    return redirect(url_for('logout'))


@app.route('/user/suspend_account')
@login_required
def suspend_account():
    user_zid = g.user['zid']

    db = get_db()
    if get_user_suspend(zid=user_zid):
        db.execute('''DELETE FROM USER_SUSPEND WHERE zid = ?''', [user_zid])

    db.execute('''INSERT INTO USER_SUSPEND
                  SELECT * FROM USER WHERE zid = ?''',
               [user_zid])
    db.execute('''DELETE FROM USER WHERE zid = ?''', [user_zid])

    db.commit()

    return redirect(url_for('user_profile', user_zid=user_zid))


@app.route('/user/activate_account')
@login_required
def activate_account():
    user_zid = g.user['zid']

    db = get_db()

    if get_user(zid=user_zid):
        db.execute('''DELETE FROM USER WHERE zid = ?''', [user_zid])

    db.execute('''INSERT INTO USER
                  SELECT * FROM USER_SUSPEND WHERE zid = ?''',
               [user_zid])
    db.execute('''DELETE FROM USER_SUSPEND WHERE zid = ?''', [user_zid])

    db.commit()

    return redirect(url_for('user_profile', user_zid=user_zid))




@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, threaded=True)
