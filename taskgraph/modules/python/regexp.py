from taskgraph.task import *
import re

@task_func
def searchPattern(
    text,
    pattern,
):
    pattern = re.compile(pattern)
    result = []
    for line in text.split('\n'):
        match = pattern.search(line)
        if match:
            groups = match.groups()
            if not groups or len(groups) < 1:
                result.append(line)
            else:
                result.append(groups[0])
    if len(result) == 1:
        return result[0]
    else:
        return '\n'.join(result)
