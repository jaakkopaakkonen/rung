import random
import smtplib
import sys
import time
import imaplib

from taskgraph.task import *


def get_email_data(length=1000):
    # Valid email characters
    chars = [bytes([i]) for i in range(1, 255)]
    # Remove to prevent \r\n mismatches
    chars.remove(b'\r')
    chars.remove(b'\n')
    # It should suffice not to post dot after newline.
    # Laziness is a terrible disease
    chars.remove(b'.')
    content = b""
    while length > 0:
        line_length = min(
            length-2,
            get_int(0, 998)
        )
        line = get_random_string(line_length, chars)
        if line_length < length:
            line += b"\r\n"
        length -= len(line)
        content += line
    return content


def get_random_string(
    length=10,
    chars=None,
):
    if chars is None:
        chars = list(b'abcdefghijklmnopqrstuvwxyz')
    result = []
    while length > 0:
        result.append(bytes(random.choice(chars)))
        length -= 1
    return b"".join(result)


def get_int(min, max):
    if max < min:
        max = min
    if min == max:
        return min
    else:
        return random.randrange(min, max + 1)


def mail_body(
    size,
    priority=None,
    Subject=None,
    Date=None,
):
    size = int(size)
    result = b""

    if Date:
        if type(Date) == str:
            Date = Date.encode("utf-8")
        result += b"Date: " + Date + b"\r\n"
    if priority:
        priority = int(priority)
        try:
            result += b"X-Priority: " + [
                None,
                b"1 (Highest)",
                b"2 (High)",
                b"3 (Normal)",
                b"4 (Low)",
                b"5 (Lowest)",
            ][int(priority)] + b"\r\n"
        except IndexError as ie:
            raise IndexError(
                "Mail priority out of bounds (1-5) inclusive"
            ) from ie
    if Subject:
        if type(Subject) == str:
            # TODO Add proper mime encoding when subject is not ascii
            Subject = Subject.encode("utf-8")
        result += b"Subject: " + Subject + b"\r\n"
    if result:
        result += b"\r\n"
    result += get_email_data(size-len(result))
    return result

task(
    mail_body,
    optional_inputs=[
        "priority",
        "Subject",
        "Date",
    ]
)

# Send smtp mail
task(
    name="send_smtp_mail",
    signature=(
        lambda host, From, To, mail_body:
            smtplib.SMTP(host=host,).sendmail(
                from_addr=From,
                to_addrs=To,
                msg=mail_body,
            ),
        "host",
        "From",
        "To",
        "mail_body",
    ),
)

@task_func
def get_imap_mails(username, password, host):
    result=[]
    try:
        imap = imaplib.IMAP4(host, 143)
        imap.login(username, password)
        status, message_count_list = imap.select(
            readonly=True,
        )
        message_count_list = imap.search(None, 'ALL')
        print(message_count_list)
        for msg_number in message_count_list[1][0].split(b' '):
            print(msg_number)
            if msg_number:
                message = imap.fetch(msg_number, "(RFC822)")
                print(message)
                result.append(message)
    except imaplib.IMAP4.error as e:
        print(e)
    finally:
        if imap:
            imap.close()
            imap.logout()
    return result


@task_func
def remove_all_imap_mails(username, password, host):
    result=[]
    try:
        imap = imaplib.IMAP4(host, 143)
        imap.login(username, password)
        status, message_count_list = imap.select(
            readonly=False,
        )
        message_count_list = imap.search(None, 'ALL')
        print(message_count_list)
        for msg_number in message_count_list[1][0].split(b' '):
            print(msg_number)
            if msg_number:
                imap.store(msg_number, '+FLAGS', '\\Deleted')
        imap.expunge()
    except imaplib.IMAP4.error as e:
        print(e)
    finally:
        if imap:
            imap.close()
            imap.logout()
    return result
