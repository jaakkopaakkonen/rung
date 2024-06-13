import os
import re
import sys
import time
import taskgraph.task
import taskgraph.config

from datetime import datetime

results_in_order = list()
results_by_values = dict()

tasks_by_runner = dict()


def register_runner(runner, task):
    global tasks_by_runner
    tasks_by_runner[runner] = task

def get_logger(runner):
    return Logger(tasks_by_runner[runner])

def prefix_lines(prefix, lines):
    if isinstance(prefix, bytes) and isinstance(lines, bytes):
        result = bytes()
        newline = b'\n'
    elif isinstance(prefix, str) and isinstance(lines, str):
        result = str()
        newline = '\n'
    lines = lines.split(newline)
    i = 0
    while i < len(lines):
        if i < (len(lines)-1) or lines[i]:
            result += prefix + lines[i] + newline
        i += 1
    return result

def timestamp_to_human(timestamp):
    datetime_obj = datetime.fromtimestamp(timestamp)
    return "{:02d}".format(datetime_obj.hour) + ':'  + \
        "{:02d}".format(datetime_obj.minute) + ':' + \
        "{:02d}".format(datetime_obj.second)

def timestamp_to_utc_bytes(timestamp):
    return bytes(
        "{:.6f}".format(
            datetime.utcfromtimestamp(timestamp).timestamp(),
        ),
        "utf-8",
    )
class Logger:

    def __init__(self, task):
        self.file = None
        # Output lines collected from stdout wihtout any additions
        self.stdoutput = []
        if taskgraph.config.log_dir:
            timestamp = time.time()
            filename = str(int(datetime.utcfromtimestamp(timestamp).timestamp()))
            if task.module:
                filename += '_' + task.module
            if task.name:
                filename += '_' + task.name
            filename += ".log"
            try:
                self.file = open(taskgraph.config.log_dir + '/' + filename, 'wb')
            except FileNotFoundError:
                os.makedirs(taskgraph.config.log_dir)
                self.file = open(taskgraph.config.log_dir + '/' + filename, 'wb')

    def print_operation(self, timestamp, operation=b'', data=b''):
        if self.file:
            self.file.write(
                prefix_lines(
                    timestamp_to_utc_bytes(timestamp) + b' ' + operation + b' ',
                    data,
                )
            )
        return prefix_lines(
            timestamp_to_human(timestamp) + ' ',
            data.decode("utf-8"),
        )

    def command(self, command):
        sys.stdout.write(
            self.print_operation(time.time(), b"CMD", command),
        )

    def pid(self, pid):
        self.print_operation(time.time(), b"PID", bytes(str(pid), "utf-8"))

    def stdout(self, output):
        self.stdoutput.append(output)
        sys.stdout.write(
            self.print_operation(time.time(), b"OUT", output),
        )

    def stderr(self, output):
        sys.stderr.write(
            self.print_operation(time.time(), b"ERR", output),
        )

    def exitcode(self, status):
        sys.stdout.write(
            self.print_operation(time.time(), b"END", bytes(str(status), "utf-8")),
        )

    def close(self):
        self.print_operation(time.time())
        self.file.close()
        return b''.join(self.stdoutput).decode("utf-8")


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
    global results_by_values
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
    global results_by_values
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
