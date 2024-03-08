import smtplib
from email.header import decode_header, make_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from retry import retry

from main import logger


@retry((smtplib.SMTPConnectError, smtplib.SMTPHeloError), 3, 5, backoff=3, logger=logger)
def send_mail(receipt, subject, content=None, sender=None,
              smtp_host=None, smtp_port=465, smtp_username=None, smtp_password=None):
    logger.debug(f'Send mail: {subject} -> {receipt}')
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receipt
    if content:
        msg.attach(MIMEText(content, 'html', 'utf-8'))
    with smtplib.SMTP_SSL(smtp_host, smtp_port) as s:
        s.login(smtp_username, smtp_password)
        s.send_message(msg)


def get_text_body(msg):
    body = ""
    charsets = msg.get_charsets()
    if msg.is_multipart():
        index = 0
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            # skip any text/plain (txt) attachments
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                body = part.get_payload(decode=True).decode(charsets[index])
                break
            index += 1
    # not multipart - i.e. plain text, no attachments
    else:
        body = msg.get_payload(decode=True).decode(0)
    return body


def get_text_header(data):
    return str(make_header(decode_header(data)))
