import logging
import pprint

import taskgraph.dag
import taskgraph.task


logging = logging.getLogger("taskgraph")
logging.setLevel(1)

all_tasks = []
all_inputs = set()


def add_task(task):
    taskgraph.dag.add(task)


def get_tasks_with_name(name):
    global all_tasks
    tasks = []
    for candidate in all_taks:
        if candidate.name == name:
            tasks.append(candidate)
    return tasks


def get_all_missing_input_build_chains(
    task,
    *valuedicts
):
    build_chains = []
    missing_inputs = task.get_missing_inputs(
        *valuedicts,
    )
    for prerequisite in missing_inputs:
        build_chain = get_build_chains(
            prerequisite,
            *valuedicts
        )
        if not build_chain:
            # Prerequisite could not be filled
            return None
        build_chains.extend(build_chain)
    return build_chains


def get_build_chains(
    name=None,
    *valuedicts,
):
    """ Get chain of tasks which will end lead (and include) name.

        When multiple tasks are defined with with same required name,
        the task which has most inputs and
        still can be fulfilled with valuedicts is used
    """
    current_build_chain = []
    # Get tasks with most inputs first
    candidates = sorted(
        get_tasks_with_name(name),
        reverse=True,
    )
    if not candidates:
        return None
    else:
        chain = None
        candidate = None
        for candidate in candidates:
            chain = get_all_missing_input_build_chains(
                candidate,
                *valuedicts
            )
            if chain is not None:
                # Found a chain for candidate
                break
        if chain is None:
            return None
        current_build_chain.append(candidate)
        current_build_chain.extend(chain)
    logging.warning(
        "get_build_chains(" + name + "): " +
        " ".join([s.name for s in current_build_chain])
    )
    return current_build_chain


def argument_subset(values, argument_names):
    """ Construct and return a subset of dictionary values
        containing only keys listed in argument_names.
    """
    result = {}
    for argument in argument_names:
        key = argument
        if isinstance(argument_names, dict):
            argument = argument_names[argument]
            if argument in values:
                argument = values[argument]
                result[key] = argument
        elif argument in values:
            result[key] = values[argument]
    return result


def run_task(
    name=None,
    *valuedicts,
):
    # logging.warning("run_task("+name+")")
    # logging.warning("with values")
    # logging.warning(pprint.pformat(valuedicts))
    return_value = None
    build_chains = get_build_chains(
        name,
        *valuedicts,
    )
    if not build_chains:
        logging.error("Could not find task " + str(name))
        logging.error("fitting values ")
        logging.error(pprint.pformat(*valuedicts))
    else:
        build_chains.reverse()
        for runtask in build_chains:
            return_value = runtask.run(*valuedicts)
    return return_value


def keys_from_dicts(*valuedicts):
    inputs = set()
    for d in valuedicts:
        inputs.update(d.keys())
    return inputs
