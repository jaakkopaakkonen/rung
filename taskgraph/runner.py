import copy
import logging
import time
import taskgraph.dag
import taskgraph.results
from taskgraph.util import log_string

log = logging.getLogger("taskgraph")

class MissingInputException(BaseException):
    # TODO: Add both input and task name information both in instance
    # and also to output print
    pass

def flatten_values(values):
    values = copy.deepcopy(values)
    result = dict()
    for key in values:
        if isinstance(values[key], dict):
            result.update(
                flatten_values(values[key])
            )
            try:
                result[key] = values[key]["result"]
                del(values[key]["result"])
            except KeyError:
                pass
            try:
                del(values[key]["startTime"])
            except KeyError:
                pass
            try:
                del(values[key]["endTime"])
            except KeyError:
                pass
        else:
            if key not in ("result", "startTime", "endTime"):
                result[key] = values[key]
    return result


class ValueTask:
    """Class which' instances contain both a single task and it's
    already fixed input values..
    The input value may be either a string or another ValueTask which
    needs to be completed in order to fulfull the value of that specific input.
    """

    @classmethod
    def create_value_task(cls, name, values={}):
        """Creates ValueTask instance from task and given dict of input values.
        Makes a copy of input values and stores only those values which
        are actually required for the execution of the task.

        :param name: The task name of the actual task used.
        :param values: Dictionary of the input values.
        """
        completed_values = dict()
        task = taskgraph.dag.get_task(name)

        # Construct all values combining the input values and
        # possible provided values of the task
        all_values = {**values}
        if task and task.provided_values:
            all_values.update(task.provided_values)
        all_task_inputs = task.input_names + task.optional_input_names
        for input_name in all_task_inputs:
            if input_name in all_values:
                if taskgraph.dag.is_task(all_values[input_name]):
                    # Input value is a task
                    completed_values[input_name] = cls.create_value_task(
                        name=all_values[input_name],
                        values=all_values,
                    )
                else:
                    completed_values[input_name] = all_values[input_name]
            elif taskgraph.dag.is_task(input_name):
                    # Either current input is actually a task name
                    # or input is not specified in inputs
                    completed_values[input_name] = cls.create_value_task(
                        name=input_name,
                        values=all_values,
                    )
            else:
                if input_name not in task.optional_input_names:
                    raise MissingInputException(input_name)
        return ValueTask(name=name, values=completed_values, task=task)

    def __init__(self, name, values={}, task=None):
        """Creates ValueTask instance from task and given dict of input values.
        Makes a copy of input values and stores only those values which
        are actually required for the execution of the task.

        :param name: The task name of the actual task used.
        :param values: Dictionary of the input values.
        """
        self.name = name
        self.values = values
        self.task = task
        if self.task is None and name:
            self.task = taskgraph.dag.get_task(name)

    def run(self):
        # TODO store results to separate structure,
        #      do not contaminate self.inputs?
        # TODO parallel execution of ValueTask inputs
        result = None
        for input_name in self.values:
            input_value = self.values[input_name]
            if isinstance(input_value, ValueTask):
                self.values[input_name] = input_value.run()
                # Store last run and evaluated input as result to handle aliases
                result = self.values[input_name]
            elif taskgraph.dag.is_task(input_value):
                print(input_value + " is task")
        if self.task.runnable:
            # Try to fetch result from the cache
            result = taskgraph.results.get_results(
                self.task,
                self.values,
            )
            if result and "result" in result:
                result = result["result"]
            # No result in cache. We need to execute
            if result == None:
                result = self.task.run(self.values)
                taskgraph.results.add(self.task, self.values, result)
        return result

    def __hash__(self):
        return hash(frozenset(self.values.items())) + hash(self.task)

    def __eq__(self, other):
        return self.values == other.values and \
            self.task == other.task

    def __deepcopy__(self, memo={}):
        values = dict()
        completed_values = dict()
        for input_name in self.values:
            input_value = self.values[input_name]
            values[input_name] = copy.deepcopy(input_value, memo)
        for input_name in self.values:
            input_value = self.values[input_name]
            completed_values[input_name] = copy.deepcopy(input_value, memo)
        result = type(self)(self.name, values)
        result.values = completed_values
        return result


class CommandLineTask(ValueTask):
    pass


