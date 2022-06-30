import inspect
import os
import types


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
    for param  in inspect.signature(
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
