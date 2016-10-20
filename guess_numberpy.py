#!/usr/bin/env python3.5
from random import randint

from flask import Flask, render_template, request, url_for

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def hello_world():
    correct = False
    message = "I've generated a number"
    if request.method == 'GET':
        # This is how you should distinguish between loading a page and submitting data
        number = randint(1, 100)
    else:
        # request.form is all the POST data. By specifying type=int, it automatically validates it for us
        number = request.form.get('number_to_guess', randint(1, 100), type=int)
        guess = request.form.get('guess', -1, type=int)
        if 0 < guess <= 100:
            if guess < number: message = 'Higher'
            elif guess > number: message = 'Lower'
            else:
                message = 'Correct'
                correct = True
        else:
            message = 'Invalid number'

    return render_template('guess.html', \
                           guess=request.form.get('guess'), \
                           correct=correct, \
                           message=message, \
                           number=number, \
                           css_path = url_for('static', filename='guess_number.css'))
@app.route('/hh', methods=['GET', 'POST'])
def hh():
    correct = False
    message = "I've generated a number"
    if request.method == 'GET':
        # This is how you should distinguish between loading a page and submitting data
        number = randint(1, 100)
    else:
        # request.form is all the POST data. By specifying type=int, it automatically validates it for us
        number = request.form.get('number_to_guess', randint(1, 100), type=int)
        guess = request.form.get('guess', -1, type=int)
        if 0 < guess <= 100:
            if guess < number: message = 'Higher'
            elif guess > number: message = 'Lower'
            else:
                message = 'Correct'
                correct = True
        else:
            message = 'Invalid number'

    return render_template('guess.html', \
                           guess=request.form.get('guess'), \
                           correct=correct, \
                           message=message, \
                           number=number, \
                           css_path = url_for('static', filename='guess_number.css'))




# your css, js, images, and anything that you wouldn't want CGI to execute, but the user should see go in the "static" directory during testing
# During production, it's advisable to set this up to be served by apache instead
@app.route('/static/<path:path>')
def send_static_file(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # you should be using this to debug. This allows you to attach an actual debugger to your script,
    # and you can see any errors that occurred in the command line. No pesky log files like cgi does
    # Also note that since use_reloader is on, you shouldn't make changes to the code while the app is paused in a debugger,
    # because it will reload as soon as you hit play again
    app.run(debug=True, use_reloader=True, host='0.0.0.0')
