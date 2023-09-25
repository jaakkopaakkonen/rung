import random
import time
from taskgraph.task import *

def get_random_ascii_data(size=80):
    size = int(size)
    result = ""
    while len(result) < size:
        val = random.randint(0, 127)
        if chr(val) in ("\r", "\n") and (len(result) + 3 < size):
            result += "\r"
            result += "\n"
            result += "A"
        else:
            result += chr(val)
    return result

# Get random ascii data based on defined length in bytes
Task(
    name="data",
    signature=(
        get_random_ascii_data,
        "size",
    ),
)

Task(
    name="wait",
    signature=(
        lambda secs: time.sleep(float(secs)),
        "secs",
    ),
)
