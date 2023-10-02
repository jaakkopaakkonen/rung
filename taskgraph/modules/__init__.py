import collections
import glob
import json
import logging
import os
import pathlib
import pprint

import taskgraph.task

log = logging.getLogger("taskgraph")

def is_executable(filepath):
    try:
        return filepath.exists() and \
            filepath.is_file() and \
            os.access(filepath, os.R_OK)
    except PermissionError:
        return False


# Dictionary with simple command as key and full path to executable as value
command_to_full_path = collections.OrderedDict()


def refresh_path_executables(paths=None):
    global command_to_full_path
    if paths is None:
        paths = os.environ.get("PATH").split(os.pathsep)
    for dir in paths:
        dir = pathlib.Path(dir)
        if not dir.exists():
            log.warning(
                "Non-existing directory " + str(dir) +
                " listed PATH environment variable",
            )
        else:
            for filepath in dir.iterdir():
                if is_executable(filepath):
                    command = filepath.name
                    if not command in command_to_full_path:
                        command_to_full_path[command] = filepath


def register_json_modules(directory=None):
    global command_to_full_path
    if directory is None:
        directory = pathlib.Path(__file__).parent.resolve()
    else:
        directory = pathlib.Path(directory).resolve()
    for jsonfile in (directory / "json").iterdir():
        with jsonfile.open(mode="rb") as fp:
            taskstruct = json.load(fp)
        struct_to_task(taskstruct)


def struct_to_task(struct):
    global command_to_full_path
    if isinstance(struct, (list, tuple)):
        for substruct in struct:
            struct_to_task(substruct)
    elif isinstance(struct, dict):
        if "executable" not in struct:
            taskgraph.task.Task(**struct)
        elif struct["executable"] in command_to_full_path:
                taskgraph.task.task_shell_script(**struct)
        else:
            log.warning("Not registering task " +struct["target"] + ". Executable " + struct["executable"] + " missing from PATH.")

