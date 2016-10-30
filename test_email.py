import keys
# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'daya0576@gmail.com'
EMAIL_HOST_PASSWORD = keys.G_EMAIL_KEY
EMAIL_PORT = 587
# EMAIL_PORT = 25
EMAIL_USE_TLS = True


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


from itsdangerous import URLSafeTimedSerializer

def generate_confirmation_token(email):
    # serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    # return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])
    serializer = URLSafeTimedSerializer('key')
    return serializer.dumps(email, salt='salt')

print(generate_confirmation_token('hahah@123'))
