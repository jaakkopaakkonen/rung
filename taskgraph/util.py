import codecs
import colorama
import fcntl
import inspect
import logging
import os
import pathlib
import re
import types


import taskgraph.matrix
import taskgraph.asciitree
import taskgraph.dag

log = logging.getLogger("taskgraph")


def get_function_name_params(function):
    """Returns the name of given function. Returns None if not applicaple

    :param function:
    :return:
    """
    result = dict()
    result["runnable"] = function
    result["inputs"] =  list()
    values = dict()
    if not inspect.isfunction(function):
        return None
    for name, value in inspect.getmembers(function):
        values[name] = value
        if "__defaults__" in values and "__name__" in values:
            break
    result["name"] = values["__name__"]
    all_params = list(
        inspect.signature(
            function,
            follow_wrapped=False,
        ).parameters,
    )
    defaults_len = 0
    if "__defaults__" in values and values["__defaults__"]:
        defaults_len = len(values["__defaults__"])
    if defaults_len == 0:
        result["inputs"] = all_params
    else:
        result["inputs"] = all_params[:-defaults_len]
        result["optionalInputs"] = all_params[
            len(all_params) - defaults_len:
        ]
    return result


def get_basename_without_ext(path):
    return os.path.splitext(
        os.path.basename(path)
    )[0]


def strip_trailing_extension(str):
    """Remove trailing .ext as long as len(ext) > 0"""
    pos = str.find(".")
    if pos < len(str)-1:
        str = str[0:pos]
    return str


def is_substructure_of(substructure, superstructure):
    """ Compares given parameters and returns whether first is the sub set of
    latter.

    substructure dictionaries can miss keys but keys existing in substructure
    must exist in superstructure and values must match.

    superstructure list can have elements not in substructure in the beginning
    or the end.

    :param substructure:
    :param superstructure:
    :return: True or false depending comparison result
    """

    def print_difference_false(a, b):
        print("NOT EQUAL")
        print(a)
        print(b)
        return False

    if type(substructure) == list and \
        type(superstructure) == list:
        superlist = superstructure
        sublist = substructure
        superstartidx = 0
        if len(sublist) == 0:
            return True
        while superstartidx < len(superlist) and \
              superstartidx < (len(superlist) - len(sublist) + 1):
            # Find first match
            sublistmismatchidx = 0
            while superstartidx < len(superlist) and \
                  sublistmismatchidx < len(sublist) and \
                  superstartidx < (len(superlist) - len(sublist) + 1) and \
                  not is_substructure_of(
                    sublist[sublistmismatchidx],
                    superlist[superstartidx]
                  ):
                superstartidx += 1
            if superstartidx >= (len(superlist) - len(sublist) + 1):
                # We consumed superlist
                return False
            superstartidx += 1
            superidx = superstartidx
            # Find complete match
            submatchidx = 1
            while superidx < len(superlist) and \
                  submatchidx < len(sublist) and \
                    (
                        is_substructure_of(
                            sublist[submatchidx],
                            superlist[superidx]
                        ) or print_difference_false(
                            sublist[submatchidx],
                            superlist[superidx]
                        )
                    ):
                submatchidx += 1
                superidx += 1
            if submatchidx >= len(sublist):
                return True
        return False
    elif (
        type(substructure) == dict and
        type(superstructure) == dict
    ):
        for key in substructure:
            if (
                key in superstructure and
                not is_substructure_of(substructure[key], superstructure[key])
            ):
                return False
        return True
    else:
        try:
            return (
                substructure == superstructure or
                substructure == superstructure["result"]
            )
        except (KeyError, TypeError):
            return False


def set_stream_nonblocking(stream):
    fileno = stream.fileno()
    flags = fcntl.fcntl(fileno, fcntl.F_GETFL)
    fcntl.fcntl(fileno, fcntl.F_SETFL, flags|os.O_NONBLOCK)


def strip_dictionary_to_keys(d, keylist):
    """ Construct and return a subset of dictionary values
        containing only keys listed in argument_names.
        :param values The dictionary which' matching values are to be returnec
        :param argument_names List or strings and/or dictionaries to be included
               in returned dictionary.
               If list item is a dictionary
    """
    result = {}
    for key in keylist:
        if key in d:
            result[key] = d[key]
    return result


def keys_from_dicts(*valuedicts):
    inputs = set()
    for d in valuedicts:
        inputs.update(d.keys())
    return inputs


def get_matching_file_basenames(dir, pattern='*'):
    """ Return set of file names matching pattern dir stripped of their path and suffix.

    :param dir: Directory as pathlib.Path
    :return: set of strings of file names stripped of suffixes
    """
    basenames = set()
    for path in dir.glob(pattern):
        basenames.add(path.stem)
    return basenames


def transpose(matrix):
    result = list()
    taskgraph.matrix.fill_matrix_none_to_width(matrix)
    for row in matrix:
        row = list(row)
        row.reverse()
        result.insert(0, row)
    return taskgraph.matrix.remove_trailing_none(result)


def format_tree_box(row_items, valuestack):
    row_items = transpose(row_items)
    # get column widths
    column_lengths = [0] * len(row_items[-1])
    for row in row_items:
        col_idx = 0
        while col_idx < len(row):
            item = row[col_idx]
            if item:
                item_length = valuestack.get_printable_len(item)
                if column_lengths[col_idx] < item_length:
                    column_lengths[col_idx] = item_length
            col_idx += 1
    # get row lengths
    row_lengths = [0] * len(row_items)
    row_idx = 0
    while row_idx < len(row_items):
        row_lengths[row_idx] = len(row_items[row_idx])
        row_idx += 1
    coming_down_columns = [False] * max(row_lengths)
    # Create tree graph
    output = ""
    row_idx = 0
    while row_idx < len(row_items):
        row = row_items[row_idx]
        col_idx = 0
        while col_idx < len(coming_down_columns):
            if col_idx < len(row):
                item = row[col_idx]
                pad_length = column_lengths[col_idx]
                up = coming_down_columns[col_idx]
                if item is None:
                    output += pad_length * ' '
                    down = up
                    left = False
                    right = False
                else:
                    # Create map graphics
                    pad_length -= valuestack.get_printable_len(item)
                    output += valuestack.get_printable_form(item)
                    output += pad_length * '─'
                    left = True
                    right = (col_idx + 1) < row_lengths[row_idx]
                    down = not right and \
                       (col_idx < (len(column_lengths)-1)) and \
                       (row_idx < (len(row_items)-1))
                    coming_down_columns[col_idx] = down
            else:
                output += column_lengths[col_idx] * ' '
                left = False
                right = False
                up = coming_down_columns[col_idx]
                down = up
            output += get_crossing_char(left, up, right, down)
            col_idx += 1
        output += '\n'
        row_idx += 1
    return output

def log_string(function, locals, cls=None, thread=None):
    members = dict()
    for key, name in inspect.getmembers(function):
        members[key] = name
    print(members)


def string_to_valid_identifier(string):
    string = string.strip()
    string = re.sub('[\\s\\t\\n]+', '_', string)

    strlist = []
    for c in string:
        if not re.findall('[^0-9a-zA-Z_]', c):
            strlist.append(c)
    string = ''.join(strlist)

    string = re.sub('[^0-9a-zA-Z_]', '', string)
    string = re.sub('^[^a-zA-Z_]+', '', string)
    return string


def get_asciitree(task):
    parents = []
    for input in task.input_names + task.optional_input_names:
        input_task = taskgraph.dag.get_task(input)
        if input_task:
            parents.append(get_asciitree(input_task))
        else:
            parents.append(taskgraph.asciitree.AsciiTreeItem(contents=input))
    return taskgraph.asciitree.AsciiTreeItem(
        contents=task.name,
        parent_list=parents,
    )