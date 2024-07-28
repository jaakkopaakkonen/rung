import taskgraph.dag
import taskgraph.results

value_names = set()
environment_values = dict()
command_line_values = dict()


def add_value_names(names):
    global value_names
    value_names.update(names)


def set_environment_values(value_dict={}):
    global value_names
    global environment_values
    for name in value_dict:
        if name in value_names:
            environment_values[name] = value_dict[name]

def deprecate_input(input_name):
    """Remove a value from cache
    :param input_name:
    :return:
    """
    global environment_values
    try:
        environment_values.pop(input_name)
    except KeyError:
        pass
    try:
        command_line_values.pop(input_name)
    except KeyError:
        pass

def deprecate_input_recursive(inputs):
    """Remove value from cache.
    Removes also all values which have had this as input.

    :param inputs:
    :return:
    """
    for input in inputs:
        deprecate_input_recursive(
            taskgraph.dag.get_tasks_having_input(input),
        )
        deprecate_input(input)

def set_command_line_value(input_name, value):
    global command_line_values
    deprecate_input_recursive([input_name])
    command_line_values[input_name] = value


def get_values():
    """

    :return:
    """
    global environment_values
    global command_line_values
    result = dict()
    result.update(environment_values)
    result.update(command_line_values)
    result.update(taskgraph.results.get_all_results())
    return result


def get_value(name):
    global command_line_values
    global environment_values

    if name in command_line_values:
        return command_line_values[name]
    if name in environment_values:
        return environment_values[name]

def is_valuename(name):
    global value_names
    return name in value_names


def fetch_value(name):
    """ Fetches the value from cache or
    executes the task providing it.

    :param name:
    :return:
    """
    result = get_value(name)
    if result is None:
        task = taskgraph.dag.get_task(name)
        values = task.get_relevant_values(get_values())
        # TODO: Find a way to run dependencies first
        # has_result will raise TyypeError on missing inputs
        missing_inputs = task.get_missing_inputs(values)
        for input in missing_inputs:
            values[input] = fetch_value(input)
        if not taskgraph.results.has_result(task, values):
            result = task.run(values)
        else:
            # No result available
            result = taskgraph.results.get_result(
                task=task,
                values=values,
            )
    return result


def reset():
    global value_names
    global environment_values
    global command_line_values
    value_names = set()
    environment_values = dict()
    command_line_values = dict()

