import colorama
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


class TaskRunner:
    def __init__(self, valuestack=None):
        self.valuestack = valuestack
        self.resolved_keys = set()
        self.task_value_structure = None

    def is_value(self, name):
        return self.valuestack.is_valuename(name)

    def get_value(self, valuename):
        if self.is_value(valuename):
            return self.valuestack.get_value(valuename)

    def get_printable_len(self, name):
        value = self.get_value(name)
        if value is not None:
            return len(name) + 1 + len(value)
        return len(name)

    def get_printable_form(self, name):
        value = self.get_value(name)
        if value is not None:
            return colorama.Fore.GREEN + \
               name + \
               '=' + value + \
               colorama.Fore.RESET
        if not taskgraph.dag.is_task(name):
            return colorama.Fore.RED + \
             name + \
             colorama.Fore.RESET
        return name

    def is_runnable(self, task_name):
        result = False
        try:
            self.task_value_structure = self.create_task_value_structure(
                structure={task_name:{}},
                values=self.valuestack.get_values(),
            )
            result = True
        except AttributeError:
            pass
        return result

    def run_tasks(self, structure):
        values = dict()
        if self.valuestack:
            values = self.valuestack.get_values()
        if self.task_value_structure is None:
            self.task_value_structure = self.create_task_value_structure(
                structure=structure,
                values=values,
            )
        return self._run_task_value_structure(self.task_value_structure)

    def run_task(self, task_name):
        return self.run_tasks({task_name: {}})

    def _resolve_value(self, key, values):
        value = values[key]
        try:
            if value not in self.resolved_keys and isinstance(value, str):
                self.resolved_keys.add(key)
                nextvalue = self._resolve_value(value, values)
                value = nextvalue
        except KeyError:
            pass
        return value

    def create_task_value_structure(
        self,
        structure=dict(),
        values=dict(),
        target=None,
    ):
        """ Calculates the task-value structure with all the input values
        in place
        :param structure:
        :param values: The original values to insert to structure
        :param target: task's target which' values to be set
        :return: The actual task target-input-substructure
        """
        if isinstance(structure, list):
            result = list()
            for item in structure:
                result.append(
                    self.create_task_value_structure(item, values, target)
                )
            return result
        elif isinstance(structure, dict):
            values = dict(values)
            structure_keys = set()
            result = dict()
            for key in structure:
                if isinstance(structure[key], dict):
                    structure_keys.add(key)
                else:
                    # First round, store only input values
                    values[key] = structure[key]
            # Next process keys with dictionary value
            for key in structure_keys:
                result[key] = self.create_task_value_structure(
                    structure[key],
                    values=values,
                    target=key,
                )
            if "tasks" in structure:
                return self.create_task_value_structure(
                    structure=structure["tasks"],
                    values=values,
                    target=target,
                )
            # Process actual input of the task
            if target:
                try:
                    task = taskgraph.dag.get_task(target)
                    # Inherit values from parent main (later) task to
                    # sub (preliminary) task
                    if task.values:
                        values.update(task.values)
                    inputs = set(task.input_names)
                    all_inputs = inputs.union(set(task.optional_input_names))
                    # Add fulfilled input values to result
                    valuenames = set(values.keys())
                    for key in valuenames & all_inputs:
                        result[key] = self._resolve_value(key, values)
                    # Process missing input values
                    for key in inputs - valuenames - structure_keys:
                        result[key] = self.create_task_value_structure(
                            target=key,
                            values=values,
                        )
                except AttributeError as ae:
                    log.error("No value for \""+target+"\"")
                    raise AttributeError("No value for \""+target+"\"") from ae
            return result
        else:
            result = dict()
            try:
                valuenames = set(values.keys())
                task = taskgraph.dag.get_task(structure)
                inputs = set(task.input_names)
                all_inputs = inputs.union(set(task.optional_input_names))
                # Add fulfilled input values to result
                for key in valuenames & all_inputs:
                    result[key] = values[key]
                # Process missing input values
                for key in inputs - valuenames:
                    result[key] = self.create_task_value_structure(
                        target=key,
                        values=values,
                    )
            except AttributeError as ae:
                log.error("No value for \"" + target + "\"")
                raise AttributeError("No value for \""+target+"\"") from ae
            return {structure: result}

    def _run_task_value_structure(self, structure):
        """ Run task-value-structure given as parameter.
            Returns exactly same structure with completed values

        :param structure: Dict based structure containing both tasks and
            the values used in their execution.
        :return: Filled structure from the execution.
        """
        result = None
        if isinstance(structure, dict):
            result = dict()
            for key in structure:
                if isinstance(structure[key], dict):
                    result[key] = self._run_task_value_structure(structure[key])
                    task = taskgraph.dag.get_task(key)
                    if (task is None or task.runnable is None) \
                       and len(result[key])==1:
                        result[key] = next(iter(result[key].values()))
                    else:
                        result[key] = task.run(
                            flatten_values(result[key]),
                        )
                else:
                    task = taskgraph.dag.get_task(structure[key])
                    if task:
                        result[key] = task.run({})
                    else:
                        value = taskgraph.results.get(structure[key])
                        if value is None:
                            value = structure[key]
                        result[key] = value
        elif isinstance(structure, list):
            result = list()
            for item in structure:
                result.append(self._run_task_value_structure(item))
        return result
