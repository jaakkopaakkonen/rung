import time
import taskgraph.task


store = list()


def add(task, values, result):
    """
    Add task name, it's input values at execution time and result
    and store these, including the timestamp it was stored to memory
    :param task: Name of task that was executed
    :param values: Dictionary of values given as input to the task
    :param result: THe result value task execution returned
    :return: None
    """
    global store
    finish_timestamp = time.time()
    if isinstance(task, taskgraph.task.Task):
        task = task.name
    store.append(
        {
            "finish_timestamp": finish_timestamp,
            "task": task,
            "values": values,
            "result": result,
        },
    )


def get(task):
    """
    Get latest structure of task result and execution
    :param task: Task name
    :return: Dictionary of finish_timestamp, task, values, result
    """
    i = len(store)-1
    while i >= 0:
        if store[i]["task"] == task:
            return store[i]
        i -= 1
    return None


def get_results():
    """
    Gets a list of tuples containing task name and it's return value.
    Earlier values of same name tasks are not returned despite of result value
    :return: list(tuple(taskname, result_value))
    """
    found_tasks = set()
    results = list()
    i = len(store)-1
    while i >= 0:
        task_name = store[i]["task"]
        task_result = store[i]["result"]
        if task_name not in found_tasks and \
           task_result is not None and \
           len(task_result) <= 80:
            results.insert(0, (task_name, task_result))
            found_tasks.add(task_name)
        i -= 1
    return results
