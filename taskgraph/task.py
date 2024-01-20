import logging
log = logging.getLogger("taskgraph")
log.setLevel(1)

import taskgraph.dag
import taskgraph.results
import taskgraph.valuestack
import taskgraph.util
import taskgraph.exception

import fcntl
import os
import pprint
import re
import select
import subprocess
import sys
import time


class NonZeroExitStatus(BaseException):
    pass

def values_as_string(values):
    result = ""
    for key in values:
        value = values[key]
        if type(value) == str and len(value) > 80:
            value = value[0:80]
        result += key+"="+str(value)+"\n"
    return result


class Task:
    """ Class to wrap executable parts and their arguments to
        more controlled entities to enable testing
    """

    inline_regexp = re.compile("{([a-zA-Z0-9_]*)}")

    def __init__(
        self,
        target=None,
        runnable=None,
        inputs=[],
        optionalInputs=[],
        defaultInput=None,
        values={},
    ):
        """Add and register new task to be used as input for other tasks
        :param target to be used for executing
               the task specifically via run_task
        :param runnable: The actual executable call (function or lambda)
            and it's argument names as list or tuple of strings, or as
            dictionary of strings,
            when the input name either as task target of earlier task or name
            in values is different from the argument actual argument name.
            If dictionary format is used, the argument actual argument name
            for the executable is key and input as value.
        :param input_names: Additional input names as list,
            tuple or separate parameters, which are neccessary for this task
            but are not relayed to the signature executable call.
        """
        # The name of this task to bue used by run_task
        log.info("Registering task "+str(target))
        self.target = target

        # The actual runnable implementation extracted
        # from the first parameter in signature

        # Other mandatory input names or prerequisites for this task
        self.input_names = list(inputs)
        # Optional input names or prerequisites for this task
        self.optional_input_names = list(optionalInputs)
        self.default_input = defaultInput
        self.runnable = runnable
        self.values = dict()
        # Check values if they contain inputs to be completed
        # Mapping to generate inline tasks.
        # Key is the pattern to be matched with input values
        # which is also used as target name.
        # Value is the list of the inputs for the task to be created
        # which names are used in the pattern.
        for value_name in values:
            input_value = str(values[value_name])
            input_name_match = self.__class__.inline_regexp.search(
                input_value,
            )
            if input_name_match:
                groups = input_name_match.groups()
                if groups and len(groups) > 0:
                    inline_input_name = groups[0]
                    if inline_input_name:
                        # Store input_value to a tuple
                        # to prevent it's value inside inline_runnable
                        # to change
                        input_value_container = (input_value, )

                        def inline_runnable(**kwargs):
                            return input_value_container[0].format(**kwargs)
                        Task(
                            target=input_value,
                            runnable=inline_runnable,
                            inputs=[inline_input_name],
                        )
        self.values = values
        taskgraph.dag.add(self)

    def log_result(self, target, values):
        if target is None:
            target = "unnamed"
        if type(values) == str:
            if len(values) > 80:
                log.warning(target + "=\"" + values[0:80] + "\"...")
            else:
                log.warning(target + "=\"" + values+"\"")

    def run(self, values):
        call_args = dict()
        call_args.update(
            taskgraph.util.argument_subset(
                values,
                self.input_names + self.optional_input_names,
            )
        )
        fulfilled_dependencies = set(call_args.keys())
        missing_dependencies = set(self.input_names) - fulfilled_dependencies
        if missing_dependencies:
            # Not all parameters fullfilled
            log.warning("Not running " + self.target)
            log.warning(
                "Missing dependencies: " + " ".join(list(missing_dependencies)),
            )
            return
        log.warning("Running " + self.target)
        log.warning("with values")
        log.warning("\n" + values_as_string(call_args))

        result = ""
        if self.runnable:
            result = self.runnable(**call_args)
            self.log_result(self.target, result)
        return result

    def is_predecessor_of(self, task):
        return self.target in task.input_names

    def is_successor_of(self, task):
        return task.target in self.input_names

    def __eq__(self, other):
        if not self.target == other.target:
            return False
        if not self.input_names == other.input_names:
            return False
        if not self.optional_input_names == other.optional_input_names:
            return False
        if self.runnable != other.runnable:
            return False
        return True

    def __lt__(self, other):
        if self.target in other.input_names:
            return True
        if self.target in other.optional_input_names:
            return True
        return self.target < other.target

    def __gt__(self, other):
        if other.target in self.input_names:
            return True
        if other.target in self.optional_input_names:
            return True
        return self.target > other.target

    def __hash__(self):
        result = hash(self.target)
        for input in self.input_names:
            result += hash(input)
        for optional_input in self.optional_input_names:
            result += hash(optional_input)
        return result


def task_func(*args, **kwargs):
    def inner_func(runnable):
        determined_values =  taskgraph.util.get_function_name_params(runnable)
        determined_values.update(kwargs)
        Task(**determined_values)
    if args:
        return inner_func(args[0])
    else:
        return inner_func


def run_commands(target, commands):
    READ_SIZE = 8192
    results = list()

    output_lines = ""
    cmd_idx = 0
    while cmd_idx < len(commands):
        line = ""
        command = commands[cmd_idx].strip()
        if command:
            print("CMD " + command, file=sys.stderr)
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                encoding="utf-8",
            )
            taskgraph.util.set_stream_nonblocking(process.stdout)
            taskgraph.util.set_stream_nonblocking(process.stderr)
            stdout_fileno = process.stdout.fileno()
            stderr_fileno = process.stderr.fileno()
            prefix = ""
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
                    outhandle = None
                    out_fileno = outstream.fileno()
                    if out_fileno == stdout_fileno:
                        outhandle = sys.stdout
                    elif out_fileno == stderr_fileno:
                        outhandle = sys.stderr
                    line += outstream.read(READ_SIZE)
                    if line:
                        output_lines += line
                        line = re.sub(
                            "\n",
                            "\r\n",
                            line,
                        )
                        # print(line, end='', file=outhandle)
                        line = ""
            outstream_list, _, _ = select.select(
                [
                    process.stdout,
                    process.stderr,
                ],
                [],
                [],
            )
            for outstream in outstream_list:
                outhandle = None
                out_fileno = outstream.fileno()
                if out_fileno == stdout_fileno:
                    outhandle = sys.stdout
                elif out_fileno == stderr_fileno:
                    outhandle = sys.stderr
                line = outstream.read(READ_SIZE)
                if line:
                    output_lines += line
                    line = re.sub(
                        "\n",
                        "\r\n",
                        line,
                    )
                    line = ""
            # Non-zero exit status, break loop
            if process.returncode:
                raise(taskgraph.exception.FailedCommand(output_lines.strip()))
        cmd_idx += 1
    return output_lines.strip()


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
    target=None,
    executable=None,
    commandLineArguments=None,
    inputs=[],
    optionalInputs=[],
    defaultInput=None,
    inputDependencies=None,
    values={},
    postprocess=None,
):
    def runnable(**resolved_input_values):
        nonlocal target
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
        result = run_commands(target, completed_script_lines)
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
        target=target,
        runnable=runnable,
        inputs=inputs,
        optionalInputs=optionalInputs,
        defaultInput=defaultInput,
        values=values,
    )
