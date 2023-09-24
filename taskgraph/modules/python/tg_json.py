import json
import logging

from taskgraph.task import task_func, task_shell_script, Task


log = logging.getLogger("taskgraph")

Task(
    name="update_json_file",
    signature=(
        lambda host, From, To, mail_body:
            smtplib.SMTP(host=host,).sendmail(
                from_addr=From,
                to_addrs=To,
                msg=mail_body,
            ),
        "key",
        "value",
        "json_file",
        "mail_body",
    ),
)
