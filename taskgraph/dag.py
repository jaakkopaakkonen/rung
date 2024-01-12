import copy
import pprint
import time

import taskgraph.results

# This file contains everything related to managing the directed asyclic graph
# containing all the input names of all tasks and their target names

import logging
log = logging.getLogger("taskgraph")

# Dictionary containing set of all task target names
# which can be fulfilled by the inputs.
# Key is inputs as frozenset.
# Value is set of task target names.
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

# Task by their target name
# Key is task target name
# Value is Task object itself
tasks_by_name = dict()


all_valuenames = set()

all_input_names = set()

all_target_names = set()

def add(task):
    """ Add task to this bookkeeper
    Adding a task will enable bookkeeper to track name and inputs
    and retrieve the task based on those
    """
    global task_names_by_complete_inputs
    global mandatory_inputs_of_tasks
    global optional_inputs_of_tasks
    global tasks_by_name
    global all_valuenames
    global all_input_names
    global all_target_names
    global tasks_having_input

    target = task.target
    inputs = frozenset(task.input_names)

    all_target_names.add(target)
    all_input_names.add(inputs)
    all_valuenames.add(target)
    all_valuenames.update(inputs)
    all_valuenames.update(task.optional_input_names)

    # task_names_by_complete_inputs
    if inputs not in task_names_by_complete_inputs:
        task_names_by_complete_inputs[inputs] = set()
    task_names_by_complete_inputs[inputs].add(target)

    # inputs_of_tasks
    mandatory_inputs_of_tasks[target] = inputs
    optional_inputs_of_tasks[target] = task.optional_input_names

    # tasks_having_input
    for input in inputs:
        if input not in tasks_having_input:
            tasks_having_input[input] = set()
        tasks_having_input[input].add(target)
    tasks_by_name[target] = task


def is_task(name):
    global tasks_by_name
    return name in tasks_by_name

def get_all_value_names():
    global all_valuenames
    return all_valuenames


def get_all_target_names():
    global all_target_names
    return all_target_names


def get_all_input_names():
    global all_input_names
    return all_input_names


def get_default_input_name(target_name):
    task = get_task(target_name)
    if not task:
        return None
    return task.default_input


def get_task(target):
    """Retrieves the task based on it's name and all non-optional inputs
       Returns None if not found
    """
    global tasks_by_name

    try:
        return tasks_by_name[target]
    except KeyError:
        return None

def final_tasks():
    """Get all tasks which are not inputs to any other task

    """
    global mandatory_inputs_of_tasks
    global optional_inputs_of_tasks

    all_tasks = set()
    all_inputs = set()
    for task in mandatory_inputs_of_tasks:
        all_tasks.add(task)
        all_inputs.update(mandatory_inputs_of_tasks[task])
        try:
            all_inputs.update(optional_inputs_of_tasks[task])
        except BaseException as be:
            logging.exception(be)
    return all_tasks - all_inputs
