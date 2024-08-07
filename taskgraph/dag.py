import taskgraph.inputs
# This file contains everything related to managing the directed asyclic graph
# containing all the input names of all tasks and their names

import logging
log = logging.getLogger("taskgraph")

# Dictionary containing set of all task names
# which can be fulfilled by the inputs.
# Key is inputs as frozenset.
# Value is set of task names.
task_names_by_complete_inputs = dict()

# Dictionary of mandatory inputs by task name.
# Key is task name
# Value is a frozen set of inputs which can fulfill this task.
mandatory_inputs_of_tasks = dict()

# Dictionary of optional inputs by task.
# Key is task name
# Value is a frozen set of inputs which can fulfill this task.
optional_inputs_of_tasks = dict()

# All tasks as set in value having single input as key
tasks_having_input = dict()

# Task by their name
# Key is task name
# Value is Task object itself
tasks_by_name = dict()

all_value_names = set()


all_task_names = set()

# key is module name, value is set of tasks in module
tasks_by_modules = dict()


class NoSuchTask(BaseException):
    pass


def add(module, task):
    """ Add task to this bookkeeper
    Adding a task will enable bookkeeper to track name and inputs
    and retrieve the task based on those
    """
    global all_task_names
    global task_names_by_complete_inputs
    global mandatory_inputs_of_tasks
    global optional_inputs_of_tasks
    global tasks_by_name
    global all_value_names
    global tasks_having_input
    global tasks_by_modules

    name = task.name
    taskgraph.inputs.add_input_names(module, task.input_names)
    taskgraph.inputs.add_input_names(module, task.optional_input_names)

    if module:
        if not module in tasks_by_modules:
            tasks_by_modules[module] = set()
        tasks_by_modules[module].add(name)

    inputs = frozenset(tuple(task.input_names))

    all_task_names.add(name)
    all_value_names.add(name)
    all_value_names.update(inputs)
    all_value_names.update(frozenset(tuple(task.optional_input_names)))

    # task_names_by_complete_inputs
    if inputs not in task_names_by_complete_inputs:
        task_names_by_complete_inputs[inputs] = set()
    task_names_by_complete_inputs[inputs].add(name)

    # inputs_of_tasks
    mandatory_inputs_of_tasks[name] = inputs
    optional_inputs_of_tasks[name] = task.optional_input_names

    # tasks_having_input
    for input in task.input_names + task.optional_input_names:
        if input not in tasks_having_input:
            tasks_having_input[input] = set()
        tasks_having_input[input].add(name)

    # tasks by name
    tasks_by_name[name] = task


def reset():
    """Empty all values from dag
    :return:
    """
    global task_names_by_complete_inputs
    global mandatory_inputs_of_tasks
    global optional_inputs_of_tasks
    global tasks_having_input
    global tasks_by_name
    global all_value_names
    global all_task_names
    global tasks_by_modules
    task_names_by_complete_inputs = dict()
    mandatory_inputs_of_tasks = dict()
    optional_inputs_of_tasks = dict()
    tasks_having_input = dict()
    tasks_by_name = dict()
    all_value_names = set()
    all_task_names = set()
    tasks_by_modules = dict()

def is_task(name):
    global tasks_by_name
    return name in tasks_by_name

def get_all_value_names():
    global all_value_names
    return all_value_names


def get_all_task_names():
    global all_task_names
    return all_task_names


def get_default_input_name(task_name):
    task = get_task(task_name)
    if not task:
        return None
    return task.default_input


def get_tasks_having_input(input_name):
    global tasks_having_input
    try:
        return tasks_having_input[input_name]
    except KeyError:
        return set()


def get_task(name):
    """Retrieves the task based on it's name and all non-optional inputs
       Returns None if not found
    """
    global tasks_by_name

    try:
        return tasks_by_name[name]
    except KeyError as ke:
        raise(NoSuchTask(ke))


def run_task(name, values):
    return get_task(name).run(values)


def get_modules():
    global tasks_by_modules
    return sorted(tasks_by_modules.keys())


def final_tasks(module=None):
    """Get all tasks which are not inputs to any other task

    """
    global tasks_by_modules
    global mandatory_inputs_of_tasks
    global optional_inputs_of_tasks

    if module is None:
        tasks = mandatory_inputs_of_tasks
    else:
        tasks = sorted(tasks_by_modules[module])

    all_tasks = set()
    all_inputs = set()
    for task in tasks:
        all_tasks.add(task)
        all_inputs.update(mandatory_inputs_of_tasks[task])
        try:
            all_inputs.update(optional_inputs_of_tasks[task])
        except BaseException as be:
            logging.exception(be)
    return all_tasks - all_inputs
