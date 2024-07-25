import colorama
import taskgraph.dag

class ValueStack:
    """ValueStack stores and manages input values from
    several different layers and sources, and is responsible for
    providing them with correct overriding when needed.

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


    def set_environment_values(self, value_dict={}):
        for name in value_dict:
            if name in self.value_names:
                self.environment_values[name] = value_dict[name]

    def set_command_line_value(self, input_name, value):
        self.deprecate_input_recursive([input_name])
        self.command_line_values[input_name] = value

    def deprecate_input(self, input_name):
        """Remove a value from cache
        :param input_name:
        :return:
        """
        try:
            self.environment_values.pop(input_name)
        except KeyError:
            pass
        try:
            self.command_line_values.pop(input_name)
        except KeyError:
            pass
        except KeyError:
            pass

    def deprecate_input_recursive(self, inputs):
        """Remove value from cache.
        Removes also all values which have had this as input.

        :param inputs:
        :return:
        """
        for input in inputs:
            self.deprecate_input_recursive(
                taskgraph.dag.get_tasks_having_input(input),
            )
            self.deprecate_input(input)

    def get_values(self):
        """

        :return:
        """
        result = dict()
        result.update(self.environment_values)
        result.update(self.command_line_values)
        result.update(taskgraph.results.get_all_results())
        return result

    def get_value(self, name):
        if name in self.command_line_values:
            return self.command_line_values[name]
        if name in self.environment_values:
            return self.environment_values[name]

    def is_valuename(self, name):
        return name in self.value_names

    def fetch_value(self, name):
        """ Fetches the value from cache or
        executes the task providing it.

        :param name:
        :return:
        """
        result = self.get_value(name)
        if result is None:
            task = taskgraph.dag.get_task(name)
            values = task.get_relevant_values(self.get_values())
            # TODO: Find a way to run dependencies first
            # has_result will raise TyypeError on missing inputs
            missing_inputs = task.get_missing_inputs(values)
            for input in missing_inputs:
                values[input] = self.fetch_value(input)
            if not taskgraph.results.has_result(task, values):
                result = task.run(values)
            else:
                # No result available
                result = taskgraph.results.get_result(
                    task=task,
                    values=values,
                )
        return result
