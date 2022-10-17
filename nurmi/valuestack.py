import nurmi.dag

def values_as_string(values):
    result = ""
    for key in values:
        value = values[key]
        if type(value) == str and len(value) > 80:
            value = value[0:80]
        result += key+"="+str(value)+"\n"
    return result

class ValueStack:
    """ValueStack stores and manages input values from several different layers
    and sources, and is responsible to providing them with correct overriding
    when needed.

    The precedence of values is (higher precedence first):
    - command line values
    - internal values after creation or latest new_level_copy
    - internal values before new_level copy and so forth
    - result values
    - environment values
    """

    # Dictionary containing values defined on the command line
    command_line_values = dict()

    # Dictionary of result values when running steps
    result_values = dict()

    def __init__(self, value_names=None):
        """ New instance.

        :param value_names: List of names used as target or input names
        """
        self.value_names = value_names
        self.internal_values = [dict()]
        # Make it possible to block internal value set in higher level
        # by setting it to None
        self.blocked_values = set()
        # Dictionary containing values defined in system environment variables
        self.environment_values = dict()

    def set_environment_values(self, value_dict={}):
        for name in value_dict:
            if name in self.value_names:
                self.environment_values[name] = value_dict[name]

    @classmethod
    def set_command_line_value(cls, input_name, value):
        cls.command_line_values[input_name] = value

    def set_internal_value(self, input_name, value):
        """Set value inside a set of targets to run, eg. a json file"""

        # Setting input value to None blocks it from existence altogether
        # in this instance and every instance
        if value is None:
            self.blocked_values.add(input_name)
        else:
            if input_name in self.blocked_values:
                self.blocked_values.remove(input_name)
            self.internal_values[-1][input_name] = value

    def new_level_copy(self):
        # Return new instance of this ValueStack
        other = ValueStack(self.value_names)
        other.environment_values = self.environment_values
        other.blocked_values = set(self.blocked_values)
        other.internal_values = list(self.internal_values)
        other.internal_values.append(dict())
        return other

    def push_internal_values(self):
        self.internal_values.append(dict())

    def pop_internal_values(self):
        return self.internal_values.pop()

    def get_values(self):
        result = dict()
        result.update(self.environment_values)
        result.update(self.__class__.result_values)
        for values in self.internal_values:
            for input in values:
                if input not in self.blocked_values:
                    result[input] = values[input]
        result.update(self.__class__.command_line_values)
        return result

    def is_valuename(self, name):
        return name in self.value_names

    @classmethod
    def set_result_value(cls, target_name, value):
        cls.result_values[target_name] = value

    @classmethod
    def reset(cls):
        cls.command_line_values = dict()
        cls.result_values = dict()
