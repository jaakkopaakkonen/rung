#! /usr/bin/env python3

import importlib.util
import json
import logging
import os
import pprint
import sys

log = logging.getLogger("nurmi")
log.setLevel(1)

# Apply everything from modules


import nurmi.framework
import nurmi.util
import nurmi.config
import nurmi.values

from nurmi.modules import *


# Read and import external modules
for path in nurmi.config.read_external_modules():
    module_name = nurmi.util.get_basename_without_ext(path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


def main():
    """The main entrypoint for the program

    :return:
    """

    # TODO Print out targets and inputs if no command line arguments defined
    if len(sys.argv) > 1:
        # We have arguments
        valuereader = nurmi.values.ValueRunner(nurmi.dag.all_valuenames)
        valuereader.read_known_values_dict(dict(os.environ))
        # This holds the current input where value is going to be read next
        current_input = None
        i = 1
        while i < len(sys.argv):
            argument = sys.argv[i]
            separator_idx = argument.find("=")
            if argument.startswith("-f"):
                i += 1
                valuereader.read_json_file(sys.argv[i])
            elif separator_idx > 0:
                valuereader.read_command_line(
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
                    valuerader.read_command_line(
                        current_input,
                        argument
                    )
                    current_input = None
                # TODO: Array values with plural suffix "s"
                else:
                    valuereader.run_target(argument)
            i += 1
        valuereader.run()


if __name__ == "__main__":
    main()
