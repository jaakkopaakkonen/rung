#! /usr/bin/env python3

import glob
import importlib.util
import json
import logging
import os
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
import taskgraph.results
import taskgraph.runner
import taskgraph.modules
import taskgraph.matrix

colorama.init(autoreset=True)

# TODO: Use same scheme as below with reading external modules so that
#  we can import them with full name
# https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path

taskgraph.modules.refresh_path_executables()

from taskgraph.modules.python import *

taskgraph.config.read_config_file()

# Read and import external json modules
if taskgraph.config.external_module_dir:
    # Read and import external python modules
    for path in glob.glob(taskgraph.config.external_module_dir + "/python/*.py"):
        module_name = taskgraph.util.get_basename_without_ext(path)
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    # Read and register external json modules
    taskgraph.modules.register_json_modules(
        directory=taskgraph.config.external_module_dir + "/json",
    )


# Read and import json modules
taskgraph.modules.register_json_modules()


def print_task_tree(values, module=None):
    if module is None:
        for module in taskgraph.dag.get_modules():
            print_task_tree(values, module)
    else:
        tasks = taskgraph.dag.final_tasks(module)
        for taskname in tasks:
            task = taskgraph.dag.get_task(taskname)
            asciitree = taskgraph.util.get_asciitree(task)
            print(asciitree.get_tree())


def print_values(values=dict()):
    for name in sorted(values):
        print(name + "=" + values[name])


def main():
    """The main entrypoint for the program

    :return:
    """
    valuestack = taskgraph.valuestack.ValueStack(
        taskgraph.dag.get_all_value_names(),
    )
    valuestack.set_environment_values(dict(os.environ))
    # TODO print relevant inputs before starting on task(s)
    if len(sys.argv) == 1:
        # TODO Print also already provided inputs
        values = valuestack.get_values()
        print_values(values)
        print("\n")
        print_task_tree(valuestack)
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
                    with open(
                        os.path.expanduser(sys.argv[i]), "rb",
                    ) as jsonfile:
                        pass
                        # runner = taskgraph.runner.TaskRunner(
                        #     valuestack,
                        # )
                        # result = runner.run_tasks(json.load(jsonfile))
                        # print(
                        #     json.dumps(
                        #         result,
                        #         indent=2,
                        #         default=lambda o: str(o),
                        #     )
                        # )
                    i += 1
                elif argument.startswith("--print"):
                    i += 1
                elif separator_idx > 0:
                    # name=value assignment
                    name = argument[0:separator_idx]
                    value = argument[separator_idx+1:]
                    default_input = taskgraph.dag.get_default_input_name(
                        name,
                    )
                    if default_input is not None:
                        # We have default input
                        valuestack.set_command_line_value(
                            default_input,
                            value,
                        )
                        valuetask = taskgraph.runner.ValueTask.create_value_task(
                            name=name,
                            values=valuestack.get_values(),
                        )
                        result = valuetask.run()
                        print(
                            json.dumps(
                                result,
                                indent=2,
                                default=lambda o: str(o),
                            )
                        )
                    else:
                        # No default input
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
                        try:
                            valuetask = taskgraph.runner.ValueTask.create_value_task(
                                name=argument,
                                values=valuestack.get_values(),
                            )
                            result = valuetask.run()
                            for task, result in taskgraph.results.get_all_results():
                                if " " in result:
                                    result = '"' + result + '"'
                                print("export "+ str(task) + "=" + str(result))
                        except taskgraph.runner.MissingInputException as mie:
                            print("Missing input for task " + str(argument))
                            print(mie.args)

                i += 1
        except taskgraph.exception.FailedCommand as ex:
            print(ex)
            exit(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=1,
        format="%(filename)s::%(funcName)s:%(lineno)d %(message)s"
    )
    main()
