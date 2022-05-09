import smtplib
from nurmi.step import *


def priority_header(priority):
    priority = int(priority)
    levelstrings = [
        None,
        "1 (Highest)",
        "2 (High)",
        "3 (Normal)",
        "4 (Low)",
        "5 (Lowest)",
    ]
    return "X-Priority: "+  levelstrings[priority]


step(priority_header)


def subject_header(subject):
    return "Subject: " + subject


step(subject_header)


def mail_contents(
    data,
    priority_header="",
    subject_header="",
):
    result = []
    if priority_header:
        result.append(priority_header + "\r\n")
    if subject_header:
        result.append(subject_header + "\r\n")
    if result:
        result.append("\r\n")
    result.append(data)
    return "".join(result)


step(
    mail_contents,
    optional_inputs=[
        "priority_header",
        "subject_header"
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
