from taskgraph.task import task_func, task_shell_script

task_shell_script(
    'nmcli connection up `nmcli -terse connection|grep ":vpn:"|sed "s/:.*//"`\n',
    "vpn",
)

task_shell_script(
    "nmcli radio wifi on",
    "wifi",
)

task_shell_script(
    'nmcli device wifi connect {SSID} password "{password}"',
    "connect_wifi",
    "SSID",
    "password",
)
