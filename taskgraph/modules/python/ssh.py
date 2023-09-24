from taskgraph.task import task_func, task_shell_script

task_shell_script(
    "ssh-keyscan {host} >> ~/.ssh/known_hosts",
    "update_ssh_key",
    "remove_ssh_key",
    "host",
)

task_shell_script(
    "ssh-keygen -f ~/.ssh/known_hosts -R {host}",
    "remove_ssh_key",
    "host",
)
