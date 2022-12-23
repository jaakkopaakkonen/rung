from taskgraph.task import task_func, task_shell_script

task_shell_script(
    'nmcli connection up `nmcli -terse connection|grep ":vpn:"|sed "s/:.*//"`\n',
    "vpn",
)
