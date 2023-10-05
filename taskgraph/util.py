import fcntl
import inspect
import logging
import os
import pathlib
import types

log = logging.getLogger("taskgraph")


def get_function_name_params(function):
    """Returns the name of given function. Returns None if not applicaple

    :param function:
    :return:
    """
    result = dict()
    result["callable"] = function
    result["input_names"] =  list()
    values = dict()
    if not inspect.isfunction(function):
        return None
    for name, value in inspect.getmembers(function):
        values[name] = value
        if "__defaults__" in values and "__name__" in values:
            break
    result["target"] = values["__name__"]
    all_params = list(
        inspect.signature(
            function,
            follow_wrapped=False,
        ).parameters,
    )
    defaults_len = 0
    if "__defaults__" in values and values["__defaults__"]:
        defaults_len = len(values["__defaults__"])
    result["input_names"] = all_params[:-defaults_len]
    result["optional_input_names"] = all_params[
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


def argument_subset(values, argument_names):
    """ Construct and return a subset of dictionary values
        containing only keys listed in argument_names.
        :param values The dictionary which' matching values are to be returnec
        :param argument_names List or strings and/or dictionaries to be included
               in returned dictionary.
               If list item is a dictionary
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
