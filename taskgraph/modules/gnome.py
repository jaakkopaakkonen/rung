import git
import logging

from taskgraph.task import task_func, task_shell_script


log = logging.getLogger("taskgraph")


task_shell_script(
    "dbus-send --type=method_call --dest=org.gnome.ScreenSaver /org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock",
    "lock_screen",
)
