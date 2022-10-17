import inspect
import logging
import os
import types

log = logging.getLogger("glu")

def get_function_name_params(function):
    """Returns the name of given function. Returns None if not applicaple

    :param function:
    :return:
    """
    result = []
    if not inspect.isfunction(function):
        return None
    for name, value in inspect.getmembers(function):
        if name == "__name__":
            result.append(value)
            break
    for param in inspect.signature(
        function,
        follow_wrapped=False,
    ).parameters:
        result.append(param)
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
