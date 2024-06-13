import logging
log = logging.getLogger("taskgraph")

all_input_names = dict()


def add_input_names(module, inputs):
    global all_input_names
    for input in inputs:
        keynames = [input]
        if module:
            keynames.extend([module + input, module + '.' + input, module + '_' + input])
        for key in keynames:
            if not key in all_input_names:
                all_input_names[key] = input


def is_input(input):
    global all_input_names
    result = False
    if input in all_input_names:
        result = True
    return result


def get_simple_values(module, values):
    global all_input_names
    result = {}
    for inputname in values:
        if all_input_names[inputname]:
            simple_inputname = all_input_names[inputname]
            result[simple_inputname] = values[inputname]
    return result


def reset():
    global all_input_names
    all_input_names = dict()