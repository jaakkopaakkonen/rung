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


import taskgraph.exception
import taskgraph.util
import taskgraph.config
import taskgraph.valuestack
import taskgraph.runner
import taskgraph.modules

colorama.init(autoreset=True)

# TODO: Use same scheme as below with reading external modules so that we can import
# them with full name
# https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
from taskgraph.modules.python import *


# Read and import external modules
for path in taskgraph.config.read_external_python_modules():
    module_name = taskgraph.util.get_basename_without_ext(path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

# Read and import json modules
taskgraph.modules.refresh_path_executables()
taskgraph.modules.register_json_modules()

def print_subgraph(target, values=dict(), prefixes=("", "")):
    # TODO Turn inputs to left and tasks to right
    # TODO consider alphabetic order
    task = taskgraph.dag.get_task(target)
    if not task:
        # name is input, not a task
        if target in values:
            print(prefixes[0] + f.GREEN + target)
        else:
            print(prefixes[0] + f.RED + target)
    else:
        all_inputs = sorted(task.input_names) + sorted(task.optional_input_names)
        if not all_inputs:
            print(prefixes[0] + f.GREEN + target)
        else:
            print(prefixes[0] + target)
        i = 0
        while i < len(all_inputs):
            if i < (len(all_inputs) - 1):
                print_subgraph(
                    target=all_inputs[i],
                    values=values,
                    prefixes=(prefixes[1] + " ├─", prefixes[1] + " │ ")
                )
            else:
                print_subgraph(
                    target=all_inputs[i],
                    values=values,
                    prefixes=(prefixes[1] + " └─", prefixes[1] + "   ")
                )
            i += 1
    # Print empty line after every major task
    if prefixes == ("", ""):
        print()


def print_values(values=dict()):
    for name in sorted(values):
        print(name + "=" + values[name])


def main():
    """The main entrypoint for the program

    :return:
    """
    valuestack = taskgraph.valuestack.ValueStack(
        taskgraph.dag.all_valuenames,
    )
    valuestack.set_environment_values(dict(os.environ))
    # TODO print relevant inputs before starting on task(s)
    if len(sys.argv) == 1:
        # TODO Print also already provided inputs
        values = valuestack.get_values()
        print_values(values)
        print("\n")
        for target in sorted(taskgraph.dag.final_tasks()):
            print_subgraph(target, values=values)
    else:
        # We have arguments
        # This holds the current input where value is going to be read next
        current_input = None
        try:
            i = 1
            while i < len(sys.argv):
                argument = sys.argv[i]
                separator_idx = argument.find("=")
                if argument.startswith("-f"):
                    i += 1
                    with open(os.path.expanduser(sys.argv[i]), "rb") as jsonfile:
                        runner = taskgraph.runner.TaskRunner(
                            valuestack,
                        )
                        result = runner.run_tasks(json.load(jsonfile))
                        print(
                            json.dumps(
                                result,
                                indent=2,
                                default=lambda o: str(o),
                            )
                        )
                    i += 1
                elif separator_idx > 0:
                    name = argument[0:separator_idx]
                    value = argument[separator_idx+1:]
                    input_name = taskgraph.dag.get_assignable_target_input_name(
                        name,
                    )
                    if input_name is not None:
                        target = name
                        valuestack.set_command_line_value(
                            input_name,
                            value,
                        )
                        runner = taskgraph.runner.TaskRunner(
                            valuestack,
                        )
                        result = runner.run_task(target)
                        print(
                            json.dumps(
                                result,
                                indent=2,
                                default=lambda o: str(o),
                            )
                        )
                    else:
                        runner = taskgraph.runner.TaskRunner(valuestack)
                        if runner.is_runnable(value):
                            result = runner.run_task(value)
                            valuestack.set_result_values({name: result[value]})
                        else:
                            valuestack.set_command_line_value(
                                name,
                                value,
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
                        runner = taskgraph.runner.TaskRunner(
                            valuestack,
                        )
                        result = runner.run_task(argument)
                        print(
                            json.dumps(
                                result,
                                indent=2,
                                default=lambda o: str(o),
                            )
                        )
                i += 1
        except taskgraph.exception.FailedCommand as ex:
            print(ex)
            exit(1)
        finally:
            valuestack.print_result_values()


if __name__ == "__main__":
    logging.basicConfig(
        level=1,
        format="%(filename)s::%(funcName)s:%(lineno)d %(message)s"
    )
    main()
