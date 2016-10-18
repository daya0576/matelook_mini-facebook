# all the imports
import os
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
    DEBUG=True,
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
        all_mate_posts = query_db('SELECT time, message, full_name, m.mate_zid as zid, profile_img '
                                  'FROM POST p JOIN MATES m ON p.zid = m.mate_zid JOIN USER u ON u.zid=p.zid '
                                  'WHERE m.user_zid= ? '
                                  'ORDER BY time DESC LIMIT 10', [user_zid])

    return render_template('index.html', all_mate_posts=all_mate_posts)


@app.route('/user/<user_zid>')
def user_profile(user_zid):
    user_info = query_db('SELECT * FROM USER WHERE zid = ?',
                         [user_zid], one=True)

    user_posts = query_db('SELECT * FROM POST WHERE zid = ? ORDER BY time DESC', [user_zid])

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
    print("searching")
    """Searching for a user whose name containing a specified substring."""
    suggestion = request.args.get('search')
    if suggestion:
        print("Searching ", suggestion)
        search_users = query_db('SELECT * FROM USER WHERE full_name LIKE "%' + suggestion + '%"')
    else:
        print("no suggestion")

    return render_template('search_result.html', search_users=search_users)


if __name__ == '__main__':
    app.run()
