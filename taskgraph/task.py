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

    def __init__(
        self,
        target=None,
        signature=(),
        inputs=[],
        optional_inputs=[],
        values=None,
    ):
        """Add and register new task to be used as input for other tasks
        :param target to be used for executing the task specifically via run_task
        :param signature: The actual executable call (function or lambda)
            and it's argument names as list or tuple of strings, or as
            dictionary of strings,
            when the input name either as task target of earlier task or name
            in values is different from the argument actual argument name.
            If dictionary format is used, the argument actual argument name
            for the executable is key and input as value.
        :param inputs: Additional inputs as list, tuple or separate parameters,
            which are neccessary for this task but are not relayed to the
            signature executable call.
        """
        # The name of this task to bue used by run_task
        self.target = target
        log.info("Registering task "+str(target))

        # The actual callable implementation extracted
        # from the first parameter in signature

        # Other mandatory inputs or prerequisites for this task
        self.inputs = frozenset(inputs)
        # Optional inputs or prerequisites for this task
        self.optional_inputs = frozenset(optional_inputs)

        self.values = values
        if signature:
            if isinstance(signature, (list, tuple)):
                self.callable_implementation = signature[0]
                self.callable_arguments = signature[1:]
            else:
                self.callable_implementation = signature

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
            log.warning("Not running " + self.target)
            log.warning(
                "Missing dependencies: " + " ".join(list(missing_dependencies)),
            )
            return
        log.warning("Running " + self.target)
        log.warning("with values")
        log.warning("\n" + values_as_string(call_args))

        if self.target is None:
            result = self.callable_implementation(**call_args)
        else:
            result = self.callable_implementation(**call_args)
        self.log_result(self.target, result)
        return result

    def is_predecessor_of(self, task):
        return self.target in task.inputs

    def is_successor_of(self, task):
        return task.target in self.inputs

    def __eq__(self, other):
        if not self.target == other.target:
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
        if self.target in other.inputs:
            return True
        if self.target in other.optional_inputs:
            return True
        return self.target < other.target

    def __gt__(self, other):
        if other.target in self.inputs:
            return True
        if other.target in self.optional_inputs:
            return True
        return self.target > other.target

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
            self.target
        ) +  "(" +  ", ".join(arguments) + ")"

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        result = hash(self.target)
        for input in self.inputs:
            result += hash(input)
        for optional_input in self.optional_inputs:
            result += hash(optional_input)
        return result


def task_func(*args, **kwargs):
    def inner_func(callable_implementation):
        determined_values =  taskgraph.util.get_function_name_params(callable_implementation)
        determined_values.update(kwargs)
        Task(**determined_values)
    if args:
        return inner_func(args[0])
    else:
        return inner_func


def run_commands(target, commands):
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


def task_shell_script(**task_struct):
    def run(**inputs):
        nonlocal task_struct
        completed_script_lines = task_struct["command_line_arguments"].format(**inputs)
        completed_script_lines = completed_script_lines.split("\n")
        completed_script_lines[0] = task_struct["executable"] + ' ' + completed_script_lines[0]
        return run_commands(task_struct["target"], completed_script_lines)
    task_params = {
        "target": task_struct["target"],
    }
    if "inputs" in task_struct:
        task_params["signature"] = (run,) + tuple(task_struct["inputs"])
        task_params["inputs"] = task_struct["inputs"]
    else:
        task_params["signature"] = (run,)

    if "optional_inputs" in task_struct:
        task_params["optional_inputs"] = task_struct["optional_inputs"]

    return Task(**task_params)
