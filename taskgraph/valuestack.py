import taskgraph.dag

class ValueStack:
    """ValueStack stores and manages input values from several different layers
    and sources, and is responsible to providing them with correct overriding
    when needed.

    The precedence of values is (higher precedence first):
    - command line values
    - result values
    - environment values
    """

    # Dictionary containing values defined on the command line

    def __init__(self, value_names):
        """ New instance.

        :param value_names: List of names used as name or input names
        """
        self.value_names = value_names
        # Dictionary containing values defined in system environment variables
        self.environment_values = dict()
        self.command_line_values = dict()
        self.result_values = dict()

    def set_environment_values(self, value_dict={}):
        for name in value_dict:
            if name in self.value_names:
                self.environment_values[name] = value_dict[name]

    def set_command_line_value(self, input_name, value):
        self.deprecate_input_recursive([input_name])
        self.command_line_values[input_name] = value

    def deprecate_input(self, input_name):
        try:
            self.environment_values.pop(input_name)
        except KeyError:
            pass
        try:
            self.command_line_values.pop(input_name)
        except KeyError:
            pass
        try:
            self.result_values.pop(input_name)
        except KeyError:
            pass

    def deprecate_input_recursive(self, inputs):
        for input in inputs:
            self.deprecate_input_recursive(
                taskgraph.dag.get_tasks_having_input(input),
            )
            self.deprecate_input(input)

    def get_values(self):
        result = dict()
        result.update(self.environment_values)
        result.update(self.command_line_values)
        result.update(self.result_values)
        return result

    def get_value(self, name):
        if name in self.result_values:
            return self.result_values[name]
        if name in self.command_line_values:
            return self.command_line_values[name]
        if name in self.environment_values:
            return self.environment_values[name]

    def is_valuename(self, name):
        return name in self.value_names

    def set_result_values(self, result_values):
        self.result_values.update(result_values)

    def print_result_values(self):
        for value_name in self.result_values:
            print(value_name + '=' + self.result_values[value_name])

    def reset(self):
        self.command_line_values = dict()
        self.result_values = dict()
