import copy
import logging
import time
import taskgraph.dag
import taskgraph.results

log = logging.getLogger("taskgraph")

def flatten_values(values):
    values = copy.deepcopy(values)
    result = dict()
    for key in values:
        if type(values[key]) == dict:
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


class TaskRunner:
    def __init__(self, valuestack=None):
        self.valuestack = valuestack
        self.resolved_keys = set()

    def run_tasks(self, structure):
        values = dict()
        if self.valuestack:
            values = self.valuestack.get_values()
        return self._run_task_value_structure(
            self._create_task_value_structure(
                structure=structure,
                values=values,
            ),
        )

    def run_task(self, task_name):
        return self.run_tasks({task_name: {}})

    def _resolve_value(self, key, values):
        value = values[key]
        try:
            if value not in self.resolved_keys and type(value) == str:
                self.resolved_keys.add(key)
                nextvalue = self._resolve_value(value, values)
                value = nextvalue
        except KeyError:
            pass
        return value

    def _create_task_value_structure(
        self,
        structure=dict(),
        values=dict(),
        name=None,
    ):
        """ Calculates the task-value structure with all the input values
        in place
        :param structure:
        :param values: The original values to insert to structure
        :param name: task's name which' values to be set
        :return: The actual task name-input-substructure
        """
        if type(structure) == list:
            result = list()
            for item in structure:
                result.append(
                    self._create_task_value_structure(item, values, name)
                )
            return result
        elif type(structure) == dict:
            values = dict(values)
            dictkeys = set()
            result = dict()
            for key in structure:
                if type(structure[key]) == dict:
                    dictkeys.add(key)
                else:
                    # First round, store only input values
                    values[key] = structure[key]
            # Next process keys with dictionary value
            for key in dictkeys:
                result[key] = self._create_task_value_structure(
                    structure[key],
                    values=values,
                    name=key,
                )
            if "tasks" in structure:
                return self._create_task_value_structure(
                    structure["tasks"],
                    values,
                    name,
                )
            # Process actual input of the task
            if name:
                try:
                    valuenames = set(values.keys())
                    task = taskgraph.dag.get_task(name)
                    inputs = set(task.inputs)
                    all_inputs = inputs.union(set(task.optional_inputs))
                    # Add fulfilled input values to result
                    for key in valuenames & all_inputs:
                        result[key] = self._resolve_value(key, values)
                    # Process missing input values
                    for key in inputs - valuenames - dictkeys:
                        result[key] = self._create_task_value_structure(
                            name=key,
                            values=values,
                        )
                except AttributeError as ae:
                    log.error("No value for \""+name+"\"")
                    raise AttributeError("No value for \""+name+"\"") from ae
            return result
        else:
            result = dict()
            try:
                valuenames = set(values.keys())
                task = taskgraph.dag.get_task(structure)
                inputs = set(task.inputs)
                all_inputs = inputs.union(set(task.optional_inputs))
                # Add fulfilled input values to result
                for key in valuenames & all_inputs:
                    result[key] = values[key]
                # Process missing input values
                for key in inputs - valuenames:
                    result[key] = self._create_task_value_structure(
                        name=key,
                        values=values,
                    )
            except AttributeError as ae:
                log.error("No value for \""+name+"\"")
                raise AttributeError("No value for \""+name+"\"") from ae
            return {structure: result}

    def _run_task_value_structure(self, structure):
        """ Run task-value-structure given as parameter.
        Fills out "startTime", "result" and "endTime" keys for tasks
        from the execution.

        :param structure: Dict based structure containing both tasks and
            the values used in their execution.
        :return: Filled structure from the execution.
        """
        values = None
        if type(structure) == dict:
            values = dict()
            for key in structure:
                if type(structure[key]) == dict:
                    values[key] = self._run_task_value_structure(structure[key])
                    task = taskgraph.dag.get_task(key)
                    values[key]["startTime"] = time.time()
                    values[key]["result"] = task.run(
                        flatten_values(values[key]),
                        self.valuestack,
                    )
                    values[key]["endTime"] = time.time()
                    log_values = taskgraph.results.process_results(
                        key,
                        values[key],
                    )
                    self.valuestack.set_result_values(log_values)
                    if not taskgraph.results.executed_successfully(values[key]):
                        break
                else:
                    value = taskgraph.results.get(structure[key])
                    if value is None:
                        value = structure[key]
                    values[key] = value
        elif type(structure) == list:
            values = list()
            for item in structure:
                values.append(run_task_value_structure(item))
        return values
