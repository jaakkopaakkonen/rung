import json
import logging

import nurmi.dag

log = logging.getLogger("nurmi")
log.setLevel(1)


class ValueRunner:
    """Class responsible for storing values provided from command line or
    json file

    """
    def __init__(self, valuenames=None):
        """Initialize ValueRunner

        :param valuenames: Names of values to be used.
        This is needed for read_known_values_dict
        """
        self.values = dict()
        if valuenames:
            self.valuenames = frozenset(valuenames)
        else:
            self.valuenames = frozenset()
        self.valuelists = list()

    def read_known_values_dict(self, values):
        """Read values from given dict, only registering those key names
        which are defined in constructor in valuenames
        :param values: Value dictionary where values are collected
        """
        for name in (set(values.keys()) & self.valuenames):
            self.values[name] = values[name]

    def read_dict(self, values):
        """Read values from dict
        :param values: Values in dict
        """
        self.values.update(values)

    def read_value(self, name, value):
        self.values[name] = value

    def read_json_file(self, filename):
        try:
            with open(filename) as fp:
                read_values = json.load(fp)
        except BaseException as be:
            log.exception(be)
        if type(read_values) == list and \
            type(read_values[0]) == dict:
                for values in read_values:
                    self.valuelists.append(values)
        elif type(read_values) == dict:
            self.read_dict(read_values)

    def read_command_line(self, name, value):
        self.values[name] = value

    def run_target(self, target):
        if self.valuelists:
            for local_values in self.valuelists:
                nurmi.dag.run_target_with_values(
                    target,
                    local_values,
                    self.values
                )
        else:
            return nurmi.dag.run_target_with_values(
                target,
                self.values
            )

    def run(self):
        targets = nurmi.dag.final_targets()
        if len(targets) > 1:
            log.warning("Several targets available:")
            log.warning(" ".join(targets))

    def has_values(self):
        return bool(self.values)
