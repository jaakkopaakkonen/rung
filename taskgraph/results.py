import time
import taskgraph.task


results_in_order = list()
results_by_values = dict()


def add(task, values, result):
    """
    Add task name, it's input values at execution time and result
    and store these, including the timestamp it was stored to memory
    :param task: Name of task that was executed
    :param values: Dictionary of values given as input to the task
    :param result: THe result value task execution returned
    :return: None
    """
    global results_in_order
    finish_timestamp = time.time()
    results_in_order.append(
        {
            "finish_timestamp": finish_timestamp,
            "task": task,
            "values": values,
            "result": result,
        },
    )
    values = values.copy()
    values["task_name"] = task.name
    results_by_values[task.get_namedtuple()(**values)] = {
        "finish_timestamp": finish_timestamp,
        "values": values,
        "result": result,
    }


def get(task):
    """
    Get latest structure of task result and execution
    :param task: Task name
    :return: Dictionary of finish_timestamp, task, values, result
    """
    i = len(results_in_order)-1
    while i >= 0:
        if results_in_order[i]["task"] == task:
            return results_in_order[i]
        i -= 1
    return None


def get_results(task, values={}):
    result = None
    try:
        values = values.copy()
        values["task_name"] = task.name
        result = results_by_values[task.get_namedtuple()(**values)]
        del(result["values"]["task_name"])
    except TypeError as te:
        # Mandatory input value missing
        pass
    except KeyError as ke:
        # No such task with such values found
        pass
    return result


def get_all_results():
    """
    Gets a list of tuples containing task name and it's return value.
    Earlier values of same name tasks are not returned despite of result value
    :return: list(tuple(taskname, result_value))
    """
    found_tasks = set()
    results = list()
    i = len(results_in_order)-1
    while i >= 0:
        task_name = results_in_order[i]["task"].name
        task_result = results_in_order[i]["result"]
        if task_name not in found_tasks and \
           task_result is not None and \
           len(task_result) <= 80:
            results.insert(0, (task_name, task_result))
            found_tasks.add(task_name)
        i -= 1
    return results
