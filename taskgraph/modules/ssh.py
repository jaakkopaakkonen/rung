from taskgraph.task import task_func, task_shell_script

task_shell_script(
    "ssh-keygen -f ~/.ssh/known_hosts -R {host}\n" +
    "ssh-keyscan {host} >> ~/.ssh/known_hosts\n",
    "update_ssh_key",
    "host",
)
