import collections
import glob
import json
import logging
import os
import pathlib
import pprint
import subprocess

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
builtin_commands = set()

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
            # Loop through all files in dir
            for filepath in dir.iterdir():
                if is_executable(filepath):
                    command = filepath.name
                    if command not in command_to_full_path:
                        command_to_full_path[command] = filepath


def register_json_modules(directory=None):
    global command_to_full_path
    if directory is None:
        directory = pathlib.Path(__file__).parent.resolve() / "json"
    else:
        directory = pathlib.Path(directory).resolve()
    for jsonfile in directory.iterdir():
        with jsonfile.open(mode="rb") as fp:
            try:
                taskstruct = json.load(fp)
                struct_to_task(jsonfile.stem, taskstruct)
            except json.decoder.JSONDecodeError:
                log.warning("Could not parse " + str(jsonfile))


def struct_to_task(module, struct):
    """Check whether struct contains executable and it is in PATH.
       If no executable or it is in PATH, relay task forward to
       task_shell_script

    :param module: Name of module where tasks are to be associated
    :param struct:
    :return:
    """
    global command_to_full_path
    if isinstance(struct, (list, tuple)):
        for substruct in struct:
            struct_to_task(module, substruct)
    elif isinstance(struct, dict):
        if "executable" not in struct:
            try:
                taskgraph.task.Task(module=module, **struct)
            except TypeError as te:
                log.exception(
                    "Task " + struct["name"] +
                    " parameters are not correct"
                )
        elif struct["executable"] in command_to_full_path or \
           is_executable(pathlib.Path(struct["executable"])):
            # Executable exists in PATH
            taskgraph.task.task_shell_script(module=module, **struct)
        else:
            log.warning(
                "Not registering task " + struct["name"] +
                ". Executable " + struct["executable"] +
                " missing from PATH.",
            )
