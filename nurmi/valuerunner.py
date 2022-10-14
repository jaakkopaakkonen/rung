import logging
import nurmi.dag
import pprint

log = logging.getLogger("nurmi")

steps_dict_key = "steps"


def run_object(object, valuestack):
    """
    :param object: Structure of lists and dicts etc. to be executed
    :param valuestack: ValueStack object
    :return: None
    """
    log.info("Evaluating object\n"+pprint.pformat(object))
    if type(object) == str:
        result = nurmi.dag.run_target_with_values(
            object,
            valuestack.get_values()
        )
        valuestack.set_result_value(
            object,
            result[object]["result"]
        )
        return result
    if type(object) == list:
        result = []
        for subobj in object:
            valuestack.push_internal_values()
            result.append(run_object(subobj, valuestack))
            valuestack.pop_internal_values()
        return result
    if type(object) == dict:
        result = {}
        # Keys in dict which' value is another dict
        dict_values = set()
        # All the rest
        other_values = set()
        for key in object:
            if type(object[key]) == dict:
                dict_values.add(key)
            elif key != steps_dict_key:
                other_values.add(key)
        for key in dict_values:
            valuestack.push_internal_values()
            result[key] = run_object(object[key], valuestack)
            values = valuestack.get_values()
            result = nurmi.dag.run_target_with_values(
                key,
                values,
            )
            if type(result) == dict and key in result:
                result = result[key]
            valuestack.set_result_value(
                key,
                result
            )
            valuestack.pop_internal_values()
        for key in other_values:
            valuestack.set_internal_value(key, object[key])
        if steps_dict_key in object:
            result["result"] = run_object(object[steps_dict_key], valuestack)
        return result
