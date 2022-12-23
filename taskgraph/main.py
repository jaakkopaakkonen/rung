#! /usr/bin/env python3

import importlib.util
import json
import logging
import os
import pprint
import sys
import colorama
from colorama import Fore as f

log = logging.getLogger("taskgraph")
log.setLevel(1)

# Apply everything from modules


import taskgraph.framework
import taskgraph.util
import taskgraph.config
import taskgraph.valuestack


colorama.init(autoreset=True)

# TODO
# Use same scheme as below with reading external modules so that we can nimport
# them with full name
# https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
# https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
from taskgraph.modules import *


# Read and import external modules
for path in taskgraph.config.read_external_modules():
    module_name = taskgraph.util.get_basename_without_ext(path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


def print_subgraph(name, values=dict(), prefixes=("", "")):
    # TODO Turn inputs to left and tasks to right
    # TODO consider alphabetic order
    task = taskgraph.dag.get_task(name)
    if not task:
        # name is input, not a task
        if name in values:
            print(prefixes[0] + f.GREEN + name)
        else:
            print(prefixes[0] + f.RED + name)
    else:
        all_inputs = sorted(task.inputs) + sorted(task.optional_inputs)
        if not all_inputs:
            print(prefixes[0] + f.GREEN + name)
        else:
            print(prefixes[0] + name)
        i = 0
        while i < len(all_inputs):
            if i < (len(all_inputs) - 1):
                print_subgraph(
                    name=all_inputs[i],
                    values=values,
                    prefixes=(prefixes[1] + " ├─", prefixes[1] + " │ ")
                )
            else:
                print_subgraph(
                    name=all_inputs[i],
                    values=values,
                    prefixes=(prefixes[1] + " └─", prefixes[1] + "   ")
                )
            i += 1
    # Print empty line after every major task
    if prefixes == ("", ""):
        print()


def main():
    """The main entrypoint for the program

    :return:
    """
    valuestack = taskgraph.valuestack.ValueStack(
        taskgraph.dag.all_valuenames
    )
    valuestack.set_environment_values(dict(os.environ))
    # TODO print relevant inputs before starting on task(s)
    if len(sys.argv) == 1:
        # TODO Print also already provided inputs
        values = valuestack.get_values()
        for name in sorted(taskgraph.dag.final_tasks()):
            print_subgraph(name, values=values)
    else:
        # We have arguments

        # This holds the current input where value is going to be read next
        current_input = None
        i = 1
        while i < len(sys.argv):
            argument = sys.argv[i]
            separator_idx = argument.find("=")
            if argument.startswith("-f"):
                i += 1
                with open(sys.argv[i], "rb") as jsonfile:
                    completed_values = \
                        taskgraph.dag.create_task_value_structure(
                            json.load(jsonfile),
                            valuestack.get_values(),
                        )
                    result = taskgraph.dag.run_task_value_structure(
                        completed_values,
                    )
                    print(
                        json.dumps(
                            result,
                            indent=2,
                            default=lambda o: str(o)
                        )
                    )
                i += 1
            elif separator_idx > 0:
                valuestack.set_command_line_value(
                    argument[0:separator_idx],
                    argument[separator_idx+1:]
                )
            elif argument.startswith("--"):
                # Value names are prefixed with --
                # Strip -- prefix
                current_input = argument[2:]
            else:
                # No argument name, perhaps it's a value or task
                if current_input:
                    # Make possible to create argument lists with plural s
                    # suffix.
                    # For instance --recipient a --recipient b ->
                    #  recipients=[a,b]
                    valuestack.set_command_line_value(
                        current_input,
                        argument,
                    )
                    current_input = None
                # TODO: Array values with plural suffix "s"
                else:
                    completed_values = \
                        taskgraph.dag.create_task_value_structure(
                            {argument: {}},
                            valuestack.get_values(),
                        )
                    result = taskgraph.dag.run_task_value_structure(
                        completed_values,
                    )
                    pprint.pprint(result)
            i += 1


if __name__ == "__main__":
    logging.basicConfig(
        level=1,
        format="%(filename)s::%(funcName)s:%(lineno)d %(message)s"
    )
    main()
