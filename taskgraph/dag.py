import copy
import pprint
import time

import taskgraph.results

# This file contains everything related to managing the directed asyclic graph
# containing all the inputs of all tasks and their names

import logging
log = logging.getLogger("taskgraph")
from taskgraph.util import strip_trailing_extension
import taskgraph.valuestack

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


all_valuenames = set()


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
    global tasks_having_input

    name = task.name
    inputs = frozenset(task.inputs)

    all_valuenames.add(name)
    all_valuenames.update(inputs)
    all_valuenames.update(task.optional_inputs)

    # task_names_by_complete_inputs
    if inputs not in task_names_by_complete_inputs:
        task_names_by_complete_inputs[inputs] = set()
    task_names_by_complete_inputs[inputs].add(name)

    # inputs_of_tasks
    mandatory_inputs_of_tasks[name] = inputs
    optional_inputs_of_tasks[name] = task.optional_inputs

    # tasks_having_input
    for input in inputs:
        if input not in tasks_having_input:
            tasks_having_input[input] = set()
        tasks_having_input[input].add(name)
    tasks_by_name[name] = task

def get_task(name):
    """Retrieves the task based on it's name and all non-optional inputs
       Returns None if not found
    """
    global tasks_by_name

    try:
        return tasks_by_name[name]
    except KeyError:
        return None

def final_tasks():
    """Get all taskss which are not inputs to any other task

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
