import random
import smtplib

from nurmi.step import *

def mail_contents(
    size,
    priority=None,
    subject=None,
):
    result = ""

    if priority:
        priority = int(priority)
        try:
            result += "X-Priority: " + [
                None,
                "1 (Highest)",
                "2 (High)",
                "3 (Normal)",
                "4 (Low)",
                "5 (Lowest)",
            ][int(priority)] + "\r\n"
        except IndexError as ie:
            raise IndexError(
                "Mail priority out of bounds (1-5) inclusive"
            ) from ie
    if subject:
        result += "Subject: " + subject + "\r\n"
    if result:
        result += "\r\n"
    size = int(size)
    size -= len(result)
    while len(result) < size:
        val = random.randint(0, 127)
        if chr(val) in ("\r", "\n") and (len(result) + 3 < size):
            result += "\r"
            result += "\n"
            result += "A"
        else:
            result += chr(val)
    return result

step(
    mail_contents,
    optional_inputs=[
        "priority",
        "subject",
    ]
)

# Send smtp mail
step(
    target="send_smtp_mail",
    signature=(
        lambda host, sender, recipients, mail_contents,:
            smtplib.SMTP(host=host,).sendmail(
                from_addr=sender,
                to_addrs=recipients,
                msg=mail_contents,
            ),
        "host",
        "sender",
        "recipients",
        "mail_contents",
    ),
)
