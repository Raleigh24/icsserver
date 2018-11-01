import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_html(recipient, sender, subject, html):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    part1 = MIMEText(html, 'html')
    msg.attach(part1)

    s = smtplib.SMTP('localhost')
    s.sendmail(sender, recipient, msg.as_string())
    s.quit()
