import logging
import threading

import taskgraph.util

# To use, annotate functions with
# @taskgraph.debug.enable_debug(logger=logging, level=logging.DEBUG)
# and enable logging with
# logging.basicConfig(level=logging.DEBUG, format="%(message)s")


indent_by_thread = dict()

def get_arguments_repr(inputs, function_args, function_kwargs):
    inputs = inputs[:]
    function_kwargs = dict(function_kwargs)
    argument_list = []
    for item in function_args:
        if isinstance(item,str):
            item = '"' + item + '"'
        argument_list.append(str(item))
    input_idx = 0
    while input_idx < len(inputs):
        key = inputs[input_idx]
        if key in function_kwargs:
            value = function_kwargs[key]
            if isinstance(value, str):
                value = '"' + value + '"'
            argument_list.append(str(key) + '=' + str(value))
            del(function_kwargs[key])
            inputs.pop(input_idx)
    for key in function_kwargs:
        value = function_kwargs[key]
        if isinstance(value, str):
            value = '"' + value + '"'
        argument_list.append(str(key) + '=' + str(value))
    return ", ".join(argument_list)


def get_function_repr(function_name, inputs, function_args, function_kwargs):
    class_instance = ''
    if inputs and \
       len(inputs) > 0 and \
        inputs[0] == "self":
        # Method
        if function_args and len(function_args) > 0:
            class_instance = function_args[0]
        inputs.pop(0)
        function_args.pop(0)
    return repr(class_instance) + '.' + function_name + '(' + get_arguments_repr(inputs, function_args, function_kwargs) + ')'


def enable_debug(logger=logging, level=logging.debug, enable=True):
    current_thread = threading.current_thread()
    if not current_thread in indent_by_thread:
        indent_by_thread[current_thread] = 0

    def enable_debug_decorator(function):
        def wrapper(*function_args, **function_kwargs):
            log_message = indent_by_thread[current_thread] * "    " + get_function_repr(
                function.__name__,
                taskgraph.util.get_function_name_params(function)["inputs"],
                list(function_args),
                function_kwargs,
            )
            logger.log(
                level,
                log_message
            )
            indent_by_thread[current_thread] += 1
            result = function(*function_args, **function_kwargs)
            logger.log(
                level,
                log_message + " = \"" + str(result) + '\"'
            )
            indent_by_thread[current_thread] -= 1
            return result
        return wrapper
    return enable_debug_decorator
