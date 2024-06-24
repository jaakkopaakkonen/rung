import logging
import threading

import taskgraph.util

indent_by_thread = dict()

def get_arguments_repr(inputs, function_args, function_kwargs):
    argument_list = []
    for item in function_args:
        argument_list.append(str(item))
    for item in inputs:
        if item in function_kwargs:
            argument_list.append(str(item) + '=' + str(function_kwargs[item]))
    return ", ".join(argument_list)


def get_function_repr(function_name, inputs, function_args, function_kwargs):
    class_name = ''
    if inputs and \
       len(inputs) > 0 and \
        inputs[0] == "self":
        # Method
        if function_args and len(function_args) > 0:
            class_instance = function_args[0]
            class_name = class_instance.__class__.__name__ + '.'
        inputs.pop(0)
        function_args.pop(0)
    return class_name + function_name + '(' + get_arguments_repr(inputs, function_args, function_kwargs) + ')'


def enable_debug(logger=logging, level=logging.debug):
    global indent_by_thread
    current_thread = threading.current_thread()
    if not current_thread in indent_by_thread:
        indent_by_thread[current_thread] = 0

    def enable_debug_decorator(function):
        def wrapper(*function_args, **function_kwargs):
            log_message = indent_by_thread[current_thread] * ' ' + get_function_repr(
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
