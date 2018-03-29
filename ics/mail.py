import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_html(to_addr, from_addr, subject, html):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr

    part1 = MIMEText(html, 'html')
    msg.attach(part1)

    s = smtplib.SMTP('localhost')
    s.sendmail(from_addr, to_addr, msg.as_string())
    s.quit()
