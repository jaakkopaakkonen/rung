import logging
log = logging.getLogger("taskgraph")
log.setLevel(1)

import collections
import re
import select
import subprocess

import taskgraph.dag
import taskgraph.inputs
import taskgraph.results
import taskgraph.values
import taskgraph.util


class NonZeroExitStatus(BaseException):
    pass

class FailedCommand(BaseException):
    pass

def values_as_string(values):
    result = ""
    for key in values:
        value = values[key]
        if type(value) == str and len(value) > 80:
            value = value[0:80]
        result += key+"="+str(value)+"\n"
    return result


def values_subset(values, value_names):
    """ Construct and return a subset of dictionary values
        containing only values which' names are listed in value_names.
        :param values The dictionary which' matching values are to be returned
        :param value_names List or strings and/or dictionaries to be included
               in returned dictionary.
               If list item is a dictionary
    """
    result = {}
    for argument in value_names:
        key = argument
        if isinstance(value_names, dict):
            argument = value_names[argument]
            if argument in values:
                argument = values[argument]
                result[key] = argument
        elif argument in values:
            result[key] = values[argument]
    return result


class Task:
    """ Class to wrap executable parts and their arguments to
        more controlled entities to enable testing
    """

    empty_input_value = object()
    @classmethod
    def create_inline_value_task(cls, name, inputs):
        """
        Creates a new task based on inputs and values

        :param name: The name of the task. The value part of the task values.
        :param inputs: List of mandatory inputs of the task
        :return:
        """
        # Search for given inputs matching {input} in given name

        task = None
        found_given_inputs = taskgraph.util.find_variables(name, inputs)
        if found_given_inputs:
            # Found given inputs
            i = 0
            while i < len(found_given_inputs):
                if found_given_inputs[i][0] == '{' and \
                   found_given_inputs[i][-1] == '}':
                    found_given_inputs[i] = found_given_inputs[i][1:-1]
                i += 1
            name_container = (name, )

            def inline_value_runnable(**kwargs):
                return name_container[0].format(**kwargs)
            task = Task(
                name=name,
                inputs=found_given_inputs,
                runnable=inline_value_runnable,
            )
        else:
            pass
        return task

    @classmethod
    def extract_input_names(cls, input_value):
        """
        Extracts patterns matching inline_regexp from string
        and returns them as list
        :param text:
        :param input_value:
        :return:
        """
        inputs = []
        for input_name_match in cls.inline_regexp.finditer(input_value):
            inputs.append(input_name_match.groups()[0])
        return inputs

    def __init__(
        self,
        name=None,
        runnable=None,
        inputs=[],
        optionalInputs=[],
        defaultInput=None,
        values={},
        module=None,
    ):
        """Add and register new task to be used as input for other tasks
        :param name to be used for executing
               the task specifically via run_task
        :param runnable: The actual executable call (function or lambda)
            and it's argument names as list or tuple of strings, or as
            dictionary of strings,
            when the input name either as task name of earlier task or name
            in values is different from the argument actual argument name.
            If dictionary format is used, the argument actual argument name
            for the executable is key and input as value.
        :param input_names: Additional input names as list,
            tuple or separate pa rameters, which are neccessary for this task
            but are not relayed to the signature executable call.
        :param values: Dictionary of input names and their values to
               be provided further down to input tasks
        """
        # The name of this task to bue used by run_task
        log.info("Registering task "+str(name))
        self.runnable = None
        self.name = name
        self.module = module
        # The actual runnable implementation extracted
        # from the first parameter in signature

        # Other mandatory input names or prerequisites for this task
        if isinstance(inputs, list):
            self.input_names = inputs[:]
        else:
            self.input_names = list(inputs)
        # Optional input names or prerequisites for this task
        self.optional_input_names = list(optionalInputs)
        taskgraph.inputs.add_input_names(
            module=self.module,
            inputs=self.input_names + self.optional_input_names,
        )
        self.default_input = defaultInput
        if runnable:
            self.runnable = runnable
            taskgraph.results.register_runner(runnable, self)
        self.provided_values = dict()
        # Check provided_values if they contain inputs to be completed
        # Mapping to generate inline tasks.
        # Key is the pattern to be matched with input values
        # which is also used as task name.
        # Value is the list of the inputs for the task to be created
        # which names are used in the pattern.
        for value_name in values:
            self.provided_values[value_name] = values[value_name]
            self.__class__.create_inline_value_task(
                name=values[value_name],
                inputs=inputs,
            )
        taskgraph.dag.add(self.module, self)

    def get_namedtuple(self, values):
        """
        Get a named tuple containing task name and it's inputs and their values
        to get hashed type mainly used for dictionary keys.
        :return: Value filled named tuple with task name in `task_name` and
            unset optional values containing "emtpy_input_value"
        """
        tupletype = collections.namedtuple(
            "task",
            ["task_name"] + self.input_names + self.optional_input_names,
            defaults=(self.empty_input_value,) * len(self.optional_input_names),
        )
        if not "task_name" in values:
            values = dict(values)
            values["task_name"] = self.name
        return tupletype(**values)

    def get_relevant_values(self, values):
        """Strip given values so that only relevant values to this task
           are included."""
        new_values = dict()
        new_values.update(
            values_subset(
                values,
                self.input_names + self.optional_input_names,
            )
        )
        return new_values

    def get_missing_inputs(self, values):
        missing_inputs = list()
        delivered_inputs = frozenset(values.keys())
        for input in self.input_names:
            if input not in delivered_inputs:
                missing_inputs.append(input)
        return missing_inputs

    def run(self, values):
        call_args = self.get_relevant_values(values)
        fulfilled_dependencies = set(call_args.keys())
        missing_dependencies = set(self.input_names) - fulfilled_dependencies
        if missing_dependencies:
            # Not all parameters fullfilled
            log.warning("Not running " + self.name)
            log.warning(
                "Missing dependencies: " + " ".join(list(missing_dependencies)),
            )
            return
        log.warning("Running " + self.name)
        log.warning("with values")
        log.warning("\n" + values_as_string(call_args))

        result = None
        if self.runnable:
            result = self.runnable(**call_args)
            taskgraph.results.add_result(self, call_args, result)
        return result

    def is_predecessor_of(self, task):
        return self.name in task.input_names

    def is_successor_of(self, task):
        return task.name in self.input_names


    def __eq__(self, other):
        if not self.name == other.name:
            return False
        if not self.input_names == other.input_names:
            return False
        if not self.optional_input_names == other.optional_input_names:
            return False
        if self.runnable != other.runnable:
            return False
        return True

    def __lt__(self, other):
        if self.name in other.input_names:
            return True
        if self.name in other.optional_input_names:
            return True
        return self.name < other.name

    def __gt__(self, other):
        if other.name in self.input_names:
            return True
        if other.name in self.optional_input_names:
            return True
        return self.name > other.name

    def __hash__(self):
        result = hash(self.name)
        for input in self.input_names:
            result += hash(input)
        for optional_input in self.optional_input_names:
            result += hash(optional_input)
        return result


class ConsecutiveTask(Task):
    @classmethod
    def create_consecutive_tasks(cls, task_names):
        consecutive_task = None
        for task in reversed(task_names):
            consecutive_task = ConsecutiveTask(
                task_name=task,
                next_consecutive_task=consecutive_task,
            )
        return consecutive_task

    def __init__(self, task_name, next_consecutive_task=None):
        self.task_name = task_name
        self.next_consecutive_task = next_consecutive_task

    def run(self):
        result = taskgraph.values.fetch_value(self.task_name)
        if self.next_consecutive_task is not None:
            self.next_consecutive_task.run()


class Condition:

    def __init__(self, input_names, evaluator, valuetask):
        self.input_names = frozenset(input_names)
        self.valuetask = valuetask
        self.evaluator = evaluator

    def can_evaluate(self, values):
        return self.input_names.issubset(frozenset(values.keys()))

    def evaluate(self, values):
        return self.evaluate(values)

    def run(self, values):
        if self.evaluator(values):
            self.next_task.run(self.task_values)


def task_func(*args, **kwargs):
    def inner_func(runnable):
        determined_values =  taskgraph.util.get_function_name_params(runnable)
        determined_values.update(kwargs)
        module = re.search(r'[^.]+$', runnable.__module__).group(0)
        Task(module=module, **determined_values)
    if args:
        return inner_func(args[0])
    else:
        return inner_func


def run_commands(logger, commands):
    READ_SIZE = 8192
    cmd_idx = 0
    while cmd_idx < len(commands):
        command = commands[cmd_idx].strip()
        if command:
            logger.command(bytes(command, "utf-8"))
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
            )
            logger.pid(process.pid)
            taskgraph.util.set_stream_nonblocking(process.stdout)
            taskgraph.util.set_stream_nonblocking(process.stderr)
            stdout_fileno = process.stdout.fileno()
            stderr_fileno = process.stderr.fileno()
            while process.poll() is None:
                outstream_list, _, _ = select.select(
                    [
                        process.stdout,
                        process.stderr,
                    ],
                    [],
                    [],
                )
                for outstream in outstream_list:
                    out_fileno = outstream.fileno()
                    if out_fileno == stdout_fileno:
                        logger.stdout(outstream.read(READ_SIZE))
                    elif out_fileno == stderr_fileno:
                        logger.stderr(outstream.read(READ_SIZE))
            outstream_list, _, _ = select.select(
                [
                    process.stdout,
                    process.stderr,
                ],
                [],
                [],
            )
            for outstream in outstream_list:
                out_fileno = outstream.fileno()
                if out_fileno == stdout_fileno:
                    logger.stdout(outstream.read(READ_SIZE))
                elif out_fileno == stderr_fileno:
                    logger.stderr(outstream.read(READ_SIZE))
            # Non-zero exit status, break loop
            logger.exitcode(process.returncode)

            if process.returncode:
                raise FailedCommand(
                    "Command \"" + command + "\" exit code: " + str(process.returncode)
                )
        cmd_idx += 1
    return logger.close()

def format_argument_list(
    argument_list,
    input_values,
    input_names=[],
    optional_input_names=[],
):
    argument_list = list(argument_list)
    arg_idx = 0
    result_argument_list = []
    combined_inputs = set(input_names).union(set(optional_input_names))
    while arg_idx < len(argument_list):
        argument = argument_list[arg_idx]
        matched_arguments = set()
        for input_name in combined_inputs:
            if '{' + input_name + '}' in argument:
                matched_arguments.add(input_name)
        if matched_arguments:
            try:
                result_argument_list.append(
                    argument.format(
                        **taskgraph.util.strip_dictionary_to_keys(
                            input_values,
                            matched_arguments,
                        )
                    )
                )
            except KeyError:
                # Input was in argument list item but no value for it
                # Skip
                pass
        else:
            result_argument_list.append(argument_list[arg_idx])
        arg_idx += 1
    return "".join(result_argument_list)


def postprocessOutput(output_lines, postprocess_rules):
    regexps = dict()
    results = list()
    current_result = dict()
    for key in postprocess_rules:
        regexps[key] = re.compile(postprocess_rules[key])
    for line in output_lines.split('\n'):
        for key in regexps:
            match = regexps[key].search(line)
            if match:
                try:
                    if key in current_result:
                        # Already result value in place
                        results.append(current_result)
                        current_result = dict()
                    current_result[key] = match.group(1)
                except IndexError:
                    pass
    results.append(current_result)
    if len(results) == 1:
        results = results[0]
    return results


def task_shell_script(
    name=None,
    executable=None,
    commandLineArguments=None,
    inputs=[],
    optionalInputs=[],
    defaultInput=None,
    values={},
    postprocess=None,
    module=None,
):
    def runnable(**resolved_input_values):
        nonlocal name
        nonlocal executable
        nonlocal commandLineArguments
        nonlocal postprocess

        if not commandLineArguments:
            completed_script_lines = [executable]
        else:
            if isinstance(commandLineArguments, list):
                completed_script_lines = format_argument_list(
                    argument_list=commandLineArguments,
                    input_values=resolved_input_values,
                    input_names=inputs,
                    optional_input_names=optionalInputs,
                )
            else:
                completed_script_lines = commandLineArguments.format(
                    **resolved_input_values,
                )
            completed_script_lines = completed_script_lines.split("\n")
            # Add the executable to the beginning of the first line
            completed_script_lines[0] = executable + ' ' + \
                completed_script_lines[0]
        # Run commands
        result = run_commands(
            taskgraph.results.get_logger(runnable),
            completed_script_lines,
        )
        if isinstance(postprocess, dict) and postprocess:
            # Resolve possible inputs in postprocess regexp pattern
            completed_inputs = dict()
            for name in postprocess:
                completed_inputs[name] = format_argument_list(
                    argument_list=[postprocess[name]],
                    input_values=resolved_input_values,
                    input_names=inputs,
                    optional_input_names=optionalInputs,
                )
            result = postprocessOutput(result, completed_inputs)
        return result
    return Task(
        module=module,
        name=name,
        runnable=runnable,
        inputs=inputs,
        optionalInputs=optionalInputs,
        defaultInput=defaultInput,
        values=values,
    )
