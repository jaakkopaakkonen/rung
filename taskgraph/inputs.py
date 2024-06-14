import logging
log = logging.getLogger("taskgraph")

all_input_names = dict()


def add_input_names(module, inputs):
    global all_input_names
    for input in inputs:
        keynames = [input]
        if module:
            keynames.extend(
                [
                    module + input,
                    module + '.' + input,
                    module + '_' + input,
                ],
            )
        for key in keynames:
            if not key in all_input_names:
                all_input_names[key] = input


def get_all_input_names():
    return frozenset(all_input_names.keys())

def is_input(input):
    global all_input_names
    result = False
    if input in all_input_names:
        result = True
    return result


def get_simple_values(module, values):
    global all_input_names
    result = {}
    for input_name in values:
        if all_input_names[input_name]:
            simple_input_name = all_input_names[input_name]
            result[simple_input_name] = values[input_name]
    return result


def reset():
    global all_input_names
    all_input_names = dict()