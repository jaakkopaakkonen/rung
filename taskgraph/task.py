import logging
log = logging.getLogger("taskgraph")
log.setLevel(1)

import taskgraph.dag
import taskgraph.results
import taskgraph.valuestack
import taskgraph.util


import fcntl
import pprint
import re
import select
import subprocess
import sys
import time


class NonZeroExitStatus(BaseException):
    pass


class Task:
    """ Class to wrap executable parts and their arguments to
        more controlled entities to enable testing
    """

    def __init__(
        self,
        name=None,
        signature=(),
        inputs=[],
        optional_inputs=[],
    ):
        """Add and register new task to be used as input for other tasks
        :param Name to be used for executing the task specifically via run_task
        :param signature: The actual executable call (function or lambda)
            and it's argument names as list or tuple of strings, or as
            dictionary of strings,
            when the input name either as task name of earlier task or name
            in values is different from the argument actual argument name.
            If dictionary format is used, the argument actual argument name
            for the executable is key and input as value.
        :param inputs: Additional inputs as list, tuple or separate parameters,
            which are neccessary for this task but are not relayed to the
            signature executable call.
        """
        # The name of this task to bue used by run_task
        self.name = None
        # The actual callable implementation extracted
        # from the first parameter in signature
        self.callable_implementation = None
        # The names of arguments for the callable implementation
        self.callable_arguments = None
        # Other mandatory inputs or prerequisites for this task
        self.inputs = None
        # Optional inputs or prerequisites for this task
        self.optional_inputs = frozenset(optional_inputs)

        if type(name) != str:
            # Assume name is function
            # Dig out the functiona name and parameter names
            inputs = taskgraph.util.get_function_name_params(name)
            new_name = inputs.pop(0)
            signature = tuple([name] + inputs)
            name = new_name
        log.info("Registering task "+str(name))
        if inputs:
            if isinstance(inputs, tuple):
                inputs = list(inputs)
            elif not isinstance(inputs, list):
                inputs = [inputs]
        if not isinstance(signature, (list, tuple)):
            self.callable_implementation = signature
        else:
            if not signature:
                self.inputs = frozenset(inputs)
            else:
                self.callable_implementation = signature[0]
                if len(signature) == 2:
                    if isinstance(signature[1], (list, tuple)):
                        arguments = signature[1]
                        self.inputs = frozenset(inputs + arguments)
                    elif isinstance(signature[1], dict):
                        arguments = signature[1]
                        inputvalues = []
                        for inputvalue in arguments.values():
                            if inputvalue:
                                inputvalues.append(inputvalue)
                        self.inputs = frozenset(
                            inputs + inputvalues
                        ) - self.optional_inputs
                    else:
                        arguments = [signature[1]]
                        self.inputs = frozenset(
                            list(inputs) + arguments
                        ) - self.optional_inputs
                else:
                    arguments = list(signature[1:])
                    self.inputs = frozenset(
                        list(inputs) + arguments
                    ) - self.optional_inputs
                self.callable_arguments = arguments
        self.name = name

    def log_result(self, name, values):
        if name is None:
            name = "unnamed"
        if type(values) == str:
            if len(values) > 80:
                log.warning(name + "=\"" + values[0:80] + "\"...")
            else:
                log.warning(name + "=\"" + values+"\"")

    def run(self, values, valuestack):
        call_args = dict()
        if self.callable_arguments:
            call_args.update(
                taskgraph.util.argument_subset(
                    values,
                    self.callable_arguments,
                )
            )
        fulfilled_dependencies = set(call_args.keys())
        missing_dependencies = self.inputs - fulfilled_dependencies
        if missing_dependencies:
            # Not all parameters fullfilled
            log.warning("Not running " + self.name)
            log.warning(
                "Missing dependencies: " + " ".join(list(missing_dependencies)),
            )
            return
        log.warning("Running " + self.name)
        log.warning("with values")
        log.warning("\n" + taskgraph.valuestack.values_as_string(call_args))

        if self.name is None:
            result = self.callable_implementation(**call_args)
        else:
            result = self.callable_implementation(**call_args)
        self.log_result(self.name, result)
        return result

    def is_predecessor_of(self, task):
        return self.name in task.inputs

    def is_successor_of(self, task):
        return task.name in self.inputs

    def __eq__(self, other):
        if not self.name == other.name:
            return False
        if not self.inputs == other.inputs:
            return False
        if self.callable_implementation != other.callable_implementation:
            return False
        if self.callable_implementation is not None and \
            (self.callable_arguments) != set(other.callable_arguments):
            return False
        return True

    def __lt__(self, other):
        if self.name in other.inputs:
            return True
        if self.name in other.optional_inputs:
            return True
        return self.name < other.name

    def __gt__(self, other):
        if other.name in self.inputs:
            return True
        if other.name in self.optional_inputs:
            return True
        return self.name > other.name

    def __repr__(self):
        arguments = []
        for arg in self.callable_arguments:
            try:
                arguments.append(
                    repr(arg) + "=" + repr(self.callable_arguments[arg])
                )
            except:
                arguments.append(repr(arg))
        return repr(
            self.name
        ) +  "(" +  ", ".join(arguments) + ")"

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        result = hash(self.name)
        for input in self.inputs:
            result += hash(input)
        for optional_input in self.optional_inputs:
            result += hash(optional_input)
        return result


def task_func(func):
    task = Task(func)
    taskgraph.dag.add(task)
    return task


def run_commands(name, commands):
    READ_SIZE = 8192
    results = list()

    cmd_idx = 0
    while cmd_idx < len(commands):
        command = commands[cmd_idx].strip()
        if command:
            command_result = dict()
            command_result["startTime"] = time.time()
            command_result["command"] = command
            command_result["log"] = list()
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
                    log_item = dict()
                    outhandle = None
                    out_fileno = outstream.fileno()
                    if out_fileno == stdout_fileno:
                        outhandle = sys.stdout
                        log_item["stream"] = "stdout"
                    elif out_fileno == stderr_fileno:
                        outhandle = sys.stderr
                        log_item["stream"] = "stderr"
                    output = outstream.read(READ_SIZE)
                    if output:
                        log_item["time"] = time.time() - \
                            command_result["startTime"]
                        log_item["data"] = output
                        command_result["log"].append(log_item)
                        output = re.sub(
                            "\n",
                            "\r\n",
                            output,
                        )
                        print(output, end='', file=outhandle)
            command_result["endTime"] = time.time()
            command_result["pid"] = process.pid
            command_result["return_code"] = process.returncode
            results.append(command_result)
            # Non-zero exit status, break loop
            if command_result["return_code"]:
                cmd_idx = len(commands)
        cmd_idx += 1
    return results


def task_shell_script(script_lines, *task_inputs):
    # TODO Do we need add name to .formatting the command line?
    name = task_inputs[0]
    inputs = task_inputs[1:]

    def run(**inputs):
        nonlocal script_lines
        completed_script_lines = script_lines.format(**inputs)
        completed_script_lines = completed_script_lines.split("\n")
        return run_commands(name, completed_script_lines)
    task = Task(name, (run,) + inputs)
    taskgraph.dag.add(task)
    return task


def task(name=None, signature=(), inputs=[], optional_inputs=[]):
    """
    Craete task and regiseter it
    :param name:
    :param signature:
    :param inputs:
    :param optional_inputs:
    :return:
    """
    task = Task(name, signature, inputs, optional_inputs)
    taskgraph.dag.add(task)