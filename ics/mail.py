import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_html(recipient, sender, subject, html):
    """Send HTML mail.

    Args:
        recipient (str): Recipient address.
        sender (str): Sender address.
        subject (str): Mail subject.
        html (str): Raw HTML to be sent.

    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    part1 = MIMEText(html, 'html')
    msg.attach(part1)

    s = smtplib.SMTP('localhost')
    s.sendmail(sender, recipient, msg.as_string())
    s.quit()
