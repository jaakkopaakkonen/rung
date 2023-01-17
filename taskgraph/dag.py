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


def retrieve_value(key, values):
    value = values[key]
    try:
        if type(value) == str:
            nextvalue = retrieve_value(value, values)
            value = nextvalue
    except KeyError:
        pass
    return value

def create_task_value_structure(
    structure=dict(),
    values=dict(),
    name=None,
):
    """ Calculates the task-value structure with all the input values
    in place
    :param structure:
    :param values: The original values to insert to structure
    :param name: task's name which' values to be set
    :return: The actual task name-input-substructure
    """
    if type(structure) == list:
        result = list()
        for item in structure:
            result.append(
                create_task_value_structure(item, values, name)
            )
        return result
    elif type(structure) == dict:
        values = dict(values)
        dictkeys = set()
        result = dict()
        for key in structure:
            if type(structure[key]) == dict:
                dictkeys.add(key)
            else:
                # First round, store only input values
                values[key] = structure[key]
        # Next process keys with dictionary value
        for key in dictkeys:
            result[key] = create_task_value_structure(
                structure[key],
                values=values,
                name=key,
            )
        if "tasks" in structure:
            return create_task_value_structure(
                structure["tasks"],
                values,
                name,
            )
        # Process actual input of the task
        if name:
            try:
                valuenames = set(values.keys())
                task = taskgraph.dag.get_task(name)
                inputs = set(task.inputs)
                all_inputs = inputs.union(set(task.optional_inputs))
                # Add fulfilled input values to result
                for key in valuenames & all_inputs:
                    result[key] = retrieve_value(key, values)
                # Process missing input values
                for key in inputs - valuenames - dictkeys:
                    result[key] = create_task_value_structure(
                        name=key,
                        values=values,
                    )
            except AttributeError as ae:
                log.error("No value for \""+name+"\"")
                raise AttributeError("No value for \""+name+"\"") from ae
        return result
    else:
        result = dict()
        try:
            valuenames = set(values.keys())
            task = taskgraph.dag.get_task(structure)
            inputs = set(task.inputs)
            all_inputs = inputs.union(set(task.optional_inputs))
            # Add fulfilled input values to result
            for key in valuenames & all_inputs:
                result[key] = values[key]
            # Process missing input values
            for key in inputs - valuenames:
                result[key] = create_task_value_structure(
                    name=key,
                    values=values,
                )
        except AttributeError as ae:
            log.error("No value for \""+name+"\"")
            raise AttributeError("No value for \""+name+"\"") from ae
        return {structure: result}


def run_task_with_values(name, values):
    log.info(
        "Running task \"" + name + "\" with values\n" +
        pprint.pformat(values)
    )
    structure = create_task_value_structure(
        task,
        values,
    )
    result = run_task_value_structure(structure)
    return result


def flatten_values(values):
    values = copy.deepcopy(values)
    result = dict()
    for key in values:
        if type(values[key]) == dict:
            result.update(flatten_values(values[key]))
            try:
                result[key] = values[key]["result"]
                del(values[key]["result"])
            except KeyError:
                pass
            try:
                del(values[key]["startTime"])
            except KeyError:
                pass
            try:
                del(values[key]["endTime"])
            except KeyError:
                pass
        else:
            if key not in ("result", "startTime", "endTime"):
                result[key] = values[key]
    return result


def run_task_value_structure(structure):
    """ Run task-value-structure given as parameter.
    Fills out "startTime", "result" and "endTime" keys for tasks
    from the execution.

    :param structure: Dict based structure containing both tasks and
        the values used in their execution.
    :return: Filled structure from the execution.
    """
    values = None
    if type(structure) == dict:
        values = dict()
        for key in structure:
            if type(structure[key]) == dict:
                values[key] = run_task_value_structure(structure[key])
                task = taskgraph.dag.get_task(key)
                values[key]["startTime"] = time.time()
                values[key]["result"] = task.run(flatten_values(values[key]))
                values[key]["endTime"] = time.time()
                taskgraph.results.add(key, values[key])
            else:
                value = taskgraph.results.get(structure[key])
                if value is None:
                    value = structure[key]
                values[key] = value

    elif type(structure) == list:
        values = list()
        for item in structure:
            values.append(run_task_value_structure(item))
    return values


def postprocess_task_result(task, result, values):
    resultdict = dict()
    resultdict[task.name] = dict()
    all_inputs = set(task.inputs)
    all_inputs.update(set(task.optional_inputs))
    for value in all_inputs & set(values.keys()):
        resultdict[task.name][value] = values[value]
    resultdict[task.name]["result"] = result
    return resultdict
