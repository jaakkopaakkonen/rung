import copy
import time
# This file contains everything related to managing the directed asyclic graph
# containing all the inputs of all steps and their targets

import logging
log = logging.getLogger("nurmi")
from nurmi.util import strip_trailing_extension
import nurmi.valuestack

# Dictionary containing set of all targets
# which can be fulfilled by the inputs.
# Key is inputs as frozenset.
# Value is set of targets.
targets_by_complete_inputs = dict()

# Dictionary of mandatory inputs by target.
# Key is target name
# Value is a frozen set of inputs which can make this target.
mandatory_inputs_of_targets = dict()

# Dictionary of optional inputs by target.
# Key is target name
# Value is a frozen set of inputs which can make this target.
optional_inputs_of_targets = dict()


# All targets as set in value having single input as key
targets_having_input = dict()

# Step by their target
# Key is target name
# Value is step
steps_by_target = dict()


all_valuenames = set()

def add(step):
    """ Add step to this bookkeeper
    Adding a step will enable bookkeeper to track target and inputs
    and retrieve the step based on those
    """
    global targets_by_complete_inputs
    global mandatory_inputs_of_targets
    global optional_inputs_of_targets
    global steps_by_target
    global all_valuenames

    target = step.target
    inputs = frozenset(step.inputs)

    all_valuenames.add(target)
    all_valuenames.update(inputs)
    all_valuenames.update(step.optional_inputs)

    # targets_by_complete_inputs
    if inputs not in targets_by_complete_inputs:
        targets_by_complete_inputs[inputs] = set()
    targets_by_complete_inputs[inputs].add(target)

    # inputs_of_targets
    mandatory_inputs_of_targets[target] = inputs
    optional_inputs_of_targets[target] = step.optional_inputs

    # targets_having_input
    for input in inputs:
        if input not in targets_having_input:
            targets_having_input[input] = set()
        targets_having_input[input].add(target)
    steps_by_target[target] = step

def get_step(target):
    """Retrieves the step based on it's target and all non-optional inputs
       Returns None if not found
    """
    global steps_by_target

    try:
        return steps_by_target[target]
    except KeyError:
        return None

def final_targets():
    """Get all targets which are not inputs to any other target

    """
    global mandatory_inputs_of_targets
    global optional_inputs_of_targets

    all_targets = set()
    all_inputs = set()
    for target in mandatory_inputs_of_targets:
        all_targets.add(target)
        all_inputs.update(mandatory_inputs_of_targets[target])
        try:
            all_inputs.update(optional_inputs_of_targets[target])
        except BaseException as be:
            logging.exception(be)
    return all_targets - all_inputs


def create_target_value_structure(
    structure=dict(),
    values=dict(),
    target=None,
):
    """ Calculates the target-value structure with all the input values in place
    :param target: Target which' values to be set
    :param values: The original values to insert to structure
    :return: The actual target-value-substructure
    """
    result = dict()
    values = dict(values)
    dictkeys = set()
    for key in structure:
        if type(structure[key]) == dict:
            dictkeys.add(key)
        else:
            # First round, store only input values
            values[key] = structure[key]
    # Next process keys with dictionary value
    for key in dictkeys:
        result[key] = create_target_value_structure(
            structure[key],
            values=values,
            target=key
        )
    # Process actual input of the target
    if target:
        try:
            valuenames = set(values.keys())
            step = nurmi.dag.get_step(target)
            inputs = set(step.inputs)
            all_inputs = inputs.union(set(step.optional_inputs))
            # Add fulfilled input values to result
            for key in valuenames & all_inputs:
                result[key] = values[key]
            # Process missing input values
            for key in inputs - valuenames - dictkeys:
                result[key] = create_target_value_structure(
                    target=key,
                    values=values,
                )
        except AttributeError as ae:
            raise AttributeError("No value for \""+target+"\"") from ae
    return result


def run_target_with_values(target, values):
    log.info(
        "Running target \"" + target + "\" with values\n" +
        pprint.pformat(values)
    )
    structure = create_target_value_structure(
        target,
        values,
    )
    result = run_target_value_structure(structure)
    return result

def flatten_values(values):
    result = dict()
    for key in values:
        if type(values[key]) == dict:
            result.update(flatten_values(values[key]))
            try:
                result[key] = values[key]["result"]
                del(values[key]["result"])
            except:
                pass
            try:
                del(values[key]["startTime"])
            except:
                pass
            try:
                del(values[key]["endTime"])
            except:
                pass
        else:
            if key not in ("result", "startTime", "endTime"):
                result[key] = values[key]
    return result


def run_target_value_structure(structure):
    """ Run target-value-structure given as parameter.
    Fills out "startTime", "result" and "endTime" keys for targets
    from the execution.

    :param structure: Dict based structure containing both targets and
    the values used in their execution
    :return: Filled structure from the execution.
    """
    values = dict()
    for key in structure:
        if type(structure[key]) == dict:
            values[key] = run_target_value_structure(structure[key])
            step = nurmi.dag.get_step(key)
            start_time = time.time()
            values[key]["result"] = step.run(flatten_values(values[key]))
            values[key]["endTime"] = time.time()
            values[key]["startTime"] = start_time
        else:
            values[key] = structure[key]
    return values


def postprocess_step_result(step, result, values):
    resultdict = dict()
    resultdict[step.target] = dict()
    all_inputs = set(step.inputs)
    all_inputs.update(set(step.optional_inputs))
    for value in all_inputs & set(values.keys()):
        resultdict[step.target][value] = values[value]
    resultdict[step.target]["result"] = result
    return resultdict
