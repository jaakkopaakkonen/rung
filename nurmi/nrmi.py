#! /usr/bin/env python3

import importlib.util
import json
import logging
import os
import pprint
import sys
import colorama
from colorama import Fore as f

log = logging.getLogger("nurmi")
log.setLevel(1)

# Apply everything from modules


import nurmi.framework
import nurmi.util
import nurmi.config
import nurmi.valuestack
import nurmi.valuerunner


colorama.init(autoreset=True)

from nurmi.modules import *


# Read and import external modules
for path in nurmi.config.read_external_modules():
    module_name = nurmi.util.get_basename_without_ext(path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


def print_subgraph(target, prefixes=("", "")):
    step = nurmi.dag.get_step(target)
    if not step:
        print(prefixes[0] + f.RED + target)
    else:
        all_inputs = sorted(step.inputs) + sorted(step.optional_inputs)
        if not all_inputs:
            print(prefixes[0] + f.RED + target)
        else:
            print(prefixes[0] + target)
        i = 0
        while i < len(all_inputs):
            if i < (len(all_inputs) - 1):
                print_subgraph(
                    all_inputs[i],
                    (prefixes[1] + " ├─", prefixes[1] + " │ ")
                )
            else:
                print_subgraph(
                    all_inputs[i],
                    (prefixes[1] + " └─", prefixes[1] + "   ")
                )
            i += 1
    # Print empty line after every major target
    if prefixes == ("", ""):
        print()


def main():
    """The main entrypoint for the program

    :return:
    """

    # TODO Print out targets and inputs if no command line arguments defined
    if len(sys.argv) == 1:
        for target in sorted(nurmi.dag.final_targets()):
            print_subgraph(target)

    else:
        # We have arguments
        valuestack = nurmi.valuestack.ValueStack(nurmi.dag.all_valuenames)
        valuestack.set_environment_values(dict(os.environ))
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
                        nurmi.dag.create_target_value_structure(
                            json.load(jsonfile),
                            valuestack.get_values(),
                        )
                    result = nurmi.dag.run_target_value_structure(
                        completed_values
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
                # No argument name, perhaps it's a value or target
                if current_input:
                    # Make possible to create argument lists with plural s
                    # suffix.
                    # For instance --recipient a --recipient b ->
                    #  recipients=[a,b]
                    valuestack.set_command_line_value(
                        current_input,
                        argument
                    )
                    current_input = None
                # TODO: Array values with plural suffix "s"
                else:
                    completed_values = \
                        nurmi.dag.create_target_value_structure(
                            {argument: {}},
                            valuestack.get_values(),
                        )
                    result = nurmi.dag.run_target_value_structure(
                        completed_values
                    )
                    pprint.pprint(result)
            i += 1


if __name__ == "__main__":
    logging.basicConfig(
        level=1,
        format="%(filename)s::%(funcName)s:%(lineno)d %(message)s"
    )
    main()
