import logging

from taskgraph.task import task_func, task_shell_script

task_shell_script(
    'ps -axo pid,command|grep -v -e chromium-browser -e kworker -e nginx -e "bash$" -e "xdg-desktop-portal" -e "gnome-terminal-server" -e "jcef_helper" -e "gvfs" -e "deja-dup" -e "gnome-settings-daemon" -e "evolution" -e "openvpn-service" -e "openvpn$" -e "loop[0-9]*" -e "/slack " -e "/slack/"',
    "list_processes",
)
