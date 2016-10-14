#!/usr/bin/env python3.5

# written by andrewt@cse.unsw.edu.au September 2016
# as a starting point for COMP2041/9041 assignment 2
# http://cgi.cse.unsw.edu.au/~cs2041/assignments/matelook/

import cgi, cgitb, glob, os

def main():
    print(page_header())
    cgitb.enable()
    users_dir = "dataset-medium"
    parameters = cgi.FieldStorage()
    print(user_page(parameters, users_dir))
    print(page_trailer(parameters))


#
# Show unformatted user for user "n".
# Increment parameter n and store it as a hidden variable
#
def user_page(parameters, users_dir):
    n = int(parameters.getvalue('n', 0))
    users = sorted(glob.glob(os.path.join(users_dir, "*")))
    user_to_show  = users[n % len(users)]
    user_filename = os.path.join(user_to_show, "user.txt")
    with open(user_filename) as f:
        user = f.read()
    return """
<div class="matelook_user_details">
%s
</div>
<p>
<form method="POST" action="">
    <input type="hidden" name="n" value="%s">
    <input type="submit" value="Next user" class="matelook_button">
</form>
""" % (user, n + 1) 


#
# HTML placed at the top of every page
#
def page_header():
    return """Content-Type: text/html

<!DOCTYPE html>
<html lang="en">
<head>
<title>matelook</title>
<link href="matelook.css" rel="stylesheet">
</head>
<body>
<div class="matelook_heading">
matelook
</div>
"""


#
# HTML placed at the bottom of every page
# It includes all supplied parameter values as a HTML comment
# if global variable debug is set
#
def page_trailer(parameters):
    html = ""
    if debug:
        html += "".join("<!-- %s=%s -->\n" % (p, parameters.getvalue(p)) for p in parameters)
    html += "</body>\n</html>"
    return html

if __name__ == '__main__':
    debug = 1
    main()
