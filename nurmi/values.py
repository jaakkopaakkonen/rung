import json
import logging

import nurmi.dag

log = logging.getLogger("nurmi")
log.setLevel(1)


class ValueRunner:

    def __init__(self, valuenames):
        self.valuenames = frozenset(valuenames)
        self.values = dict()

    def read_environment_variables(self, values):
        for name in set(values.keys()) & self.valuenames:
            self.values[name] = values[name]

    def read_json_file(self, filename):
        try:
            with open(filename) as fp:
                self.values.update(json.load(fp))
        except BaseException as be:
            log.exception(be)

    def read_command_line(self, name, value):
        self.values[name] = value

    def run_target(self, target):
        inputs = nurmi.dag.get_inputs_to_target(target)
        for input in inputs:
            if input not in self.values:
                self.values[input] = nurmi.dag.get_step(
                    input
                ).run(
                    self.values
                )


    def run(self):
        targets = nurmi.dag.final_targets()
        if len(targets) > 1:
            log.warning("Several targets available:")
            log.warning(" ".join(targets))

    def has_values(self):
        return bool(self.values)
