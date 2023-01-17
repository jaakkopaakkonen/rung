import re

# Storage which stores the result values of earlier tasks
# and thus makes them available as input values to tasks executed later on"""


store = dict()


def add(task_name=None, structure=None):
    """Store task results/inputs to the store
    """
    global store
    if task_name not in store:
        store[task_name] = dict()
    for input in structure:
        store[task_name][input] = structure[input]

def get(path, structure=None):
    """Get executed task results or inputs by json schema path
    """
    global store
    if structure is None:
        structure = store
    result = None
    if type(path) == str:
        elements = path.split('.')
        key = elements[0]
        if len(elements) == 1:
            try:
                result = structure[key]
            except KeyError:
                pass
        else:
            if type(structure) == list:
                # Strip out surrounding brackets [ ]
                key = re.sub(
                    r"\[([-0-9]*)\]",
                    r"\1",
                    key,
                )
                key = int(key)
            try:
                result = get(
                    '.'.join(elements[1:]),
                    structure[key],
                )
            except KeyError:
                pass
    return result
