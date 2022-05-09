#! /usr/bin/env python3

import importlib.util
import logging
import os
import pprint
import sys

logging = logging.getLogger("nurmi")
logging.setLevel(1)

# Apply everything from modules


import nurmi.framework
import nurmi.util
import nurmi.config

from nurmi.modules import *


# Read and import external modules
for path in nurmi.config.read_external_modules():
    module_name = nurmi.util.get_basename_without_ext(path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


def read_environment_variables():
    env = dict(os.environ)

    result = dict()
    for name in set(env.keys()) & nurmi.framework.all_inputs:
        result[name] = env[name]
    return result


def main():
    """The main entrypoint for the program

    :return:
    """

    # If no target defined, run all
    target_defined = False

    if len(sys.argv) <= 1:
        # No arguments given, print out all registered steps
        for step in nurmi.framework.all_steps:
            print(step.target + "\t" + "\t".join(sorted(step.inputs)))
    else:
        # We have arguments

        # Input values will be collected here from command line
        values = read_environment_variables()
        if values:
            print("Read environment values as input:")
            pprint.pprint(values)

        # This holds the current input where value is going to be read next
        current_input = None

        i = 1
        while i < len(sys.argv):
            argument = sys.argv[i]
            if argument.startswith("--"):
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
                    if (
                        current_input not in nurmi.framework.all_inputs
                        and current_input + "s" in nurmi.framework.all_inputs
                    ):
                        if not current_input + "s" in values:
                            values[current_input + "s"] = []
                        values[current_input + "s"].append(argument)
                    else:
                        values[current_input] = argument
                    current_input = None
                else:
                    target_defined = True
                    nurmi.framework.run_target(argument, values)
            i += 1
        if values and not target_defined:
            nurmi.framework.run_all(values)
        pprint.pprint(values)


if __name__ == "__main__":
    main()
