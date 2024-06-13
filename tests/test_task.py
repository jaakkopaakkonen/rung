import collections
import os
import pytest
import random
import sys
import time

from unittest.mock import *

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.realpath(__file__),
            "../..",
        ),
    ),
)

import taskgraph.task
import taskgraph.modules
import taskgraph.dag
import taskgraph.modules
import taskgraph.results
import taskgraph.runner


def test_format_argument_list():
    assert taskgraph.task.format_argument_list(
        argument_list = [
            "no inputs",
            " this should stay {a}",
            " this should stay too {z}",
            " this should also stay {b}",
            " this should go {c}",
        ],
        input_values = {
            "a": "and it stayed",
            "b": "and it also stayed",
        },
        input_names={"a", "b"},
        optional_input_names={"c"},
    ) == "no inputs this should stay and it stayed this should stay too {z} this should also stay and it also stayed"


@patch("taskgraph.results.Logger")
def test_task_with_command_line_parts(logger):
    module = "module"
    task_structure = {
        "name": "commit",
        "executable": "echo",
        "commandLineArguments": [
            "echo git commit --dry-run",
            " --file={commit_message_file}",
            " --message=\"{commit_message}\"",
        ],
        "optionalInputs": [
            "commit_message_file",
            "commit_message",
        ]
    }
    taskgraph.modules.command_to_full_path = {
        "echo": "/usr/bin/echo",
    }
    taskgraph.modules.struct_to_task(module, task_structure)
    task = taskgraph.dag.get_task("commit")
    result = task.run({"commit_message_file": "commit.md"})

    assert logger.return_value.command.mock_calls == [
        (
            '',
            (b'echo echo git commit --dry-run --file=commit.md',),
            {},
        )
    ]
    assert len(logger.return_value.pid.mock_calls) == 1
    assert len(logger.return_value.pid.mock_calls[0][1]) == 1
    assert logger.return_value.pid.mock_calls[0][1][0] > 0

    assert logger.return_value.stdout.mock_calls == [
        (
            '',
            (b'echo git commit --dry-run --file=commit.md\n',),
            {},
        )
    ]
    assert logger.return_value.stderr.mock_calls == [
        (
            '',
            (b'',),
            {},
        )
    ]

    assert logger.return_value.exitcode.mock_calls == [
        (
            '',
            (0,),
            {},
        )
    ]


def test_simple_task_execution():
    expected_result = "result"
    runnable = Mock(return_value=expected_result)
    inputnames = ["alpha", "beta", "gamma"]
    optionalinputnames = ["delta"]
    task = taskgraph.task.Task(
        name="testtask",
        runnable=runnable,
        inputs=inputnames,
        optionalInputs=optionalinputnames,
        defaultInput="alpha",
    )
    input_values = {"alpha": 1, "beta": 2, "gamma": 3}
    result = task.run(input_values)
    assert result == expected_result
    assert runnable.mock_calls == [
        (
            '',
            (),
            input_values,
        ),
    ]


@pytest.mark.skip
def test_task_with_values():
    taskname = "car"
    inputs = ["engine", "tyres"]
    runnable_car = Mock(
        side_effect=lambda engine, tyres: {
            "engine": engine,
            "tyres": tyres,
            "time": time.time(),
        }
    )
    values = {
        "transmission": "transmission has {gears} gears",
    }
    task_car = taskgraph.task.Task(
        name=taskname,
        runnable=runnable_car,
        inputs=inputs,
        values=values,
    )
    # Check parent task contents
    parent_task = taskgraph.dag.get_task(taskname)
    assert parent_task.input_names == ["engine", "tyres"]
    assert parent_task.provided_values == {
        "transmission": "transmission has {gears} gears",
    }
    # Run parent task
    beginning = time.time()
    result = parent_task.run(
        {
            "engine": "volvo",
            "tyres": "michelin",
        },
    )
    end = time.time()
    assert beginning < result["time"] < end
    del(result["time"])
    assert result == {
        "engine": "volvo",
        "tyres": "michelin",
    }
    assert runnable_car.mock_calls == [
        (
            '',
            (),
            {
                "engine": "volvo",
                "tyres": "michelin",
            },
        )
    ]
    # Check child task contents
    child_task = taskgraph.dag.get_task("transmission has {gears} gears")
    assert child_task.inputs == ["gears"]
    assert child_task.provided_values == {}
    # Run child task
    result = child_task.run({"gears": "four"})
    assert result == "transmission has four gears"


def test_task_inline_values():
    # Initialize command_to_full_path to bypass executable search from PATH
    old_command_to_full_path = taskgraph.modules.command_to_full_path
    taskgraph.modules.command_to_full_path = ["gnome-terminal"]

    # Initialize tasks
    taskgraph.modules.struct_to_task(
        "module",
        [
            {
                "name": "terminal",
                "executable": "gnome-terminal",
                "commandLineArguments": [
                    "--window", " --title '{title}'", " -- {command}",
                ],
                "optionalInputs": ["command", "title"],
            },
            {
                "name": "tailService",
                "inputs": ["terminal", "host", "service"],
                "values": {
                    "title": "{host}: supervisorctl tail -f {service}",
                    "command": "ssh {host} sudo supervisorctl tail -f {service}"
                },
            },
        ],
    )
    # Switch terminal runnable with a Mock
    terminal_task = taskgraph.dag.get_task("terminal")
    terminal_task.runnable = Mock()

    # Check inline title task has everything in place
    inline_title_task = taskgraph.dag.get_task(
        "{host}: supervisorctl tail -f {service}",
    )
    assert set(inline_title_task.input_names) == {"host", "service"}
    assert inline_title_task.runnable(
        host="testhost",
        service="testservice",
    ) == "testhost: supervisorctl tail -f testservice"

    # Check inline command task has everything in place
    inline_command_task = taskgraph.dag.get_task(
        "ssh {host} sudo supervisorctl tail -f {service}",
    )
    assert set(inline_command_task.input_names) == {"host", "service"}
    assert inline_command_task.runnable(
        host="testhost",
        service="testservice",
    ) == "ssh testhost sudo supervisorctl tail -f testservice"

    # Check tailService task has everything in place
    tailService_task = taskgraph.dag.get_task("tailService")
    assert set(tailService_task.input_names) == {"terminal", "host", "service"}
    assert tailService_task.provided_values == {
        "title": "{host}: supervisorctl tail -f {service}",
        "command": "ssh {host} sudo supervisorctl tail -f {service}",
    }
    valuetask = taskgraph.runner.ValueTask.create_value_task(
        name="tailService",
        values={
            "host": "www.google.com",
            "service": "searchengine",
        },
    )
    result = valuetask.run()

    # TODO: Return value does not match. Fix.
    #assert result == terminal_task.runnable.return_value
    assert terminal_task.runnable.mock_calls == [
        (
            '',
            (),
            {
                "command":
                    "ssh www.google.com sudo supervisorctl tail -f searchengine",
                "title": "www.google.com: supervisorctl tail -f searchengine",
            },
        ),
    ]
    # Revert original command_to_full_path
    taskgraph.modules.command_to_full_path = old_command_to_full_path


def test_get_namedtuple():
    # Initialize command_to_full_path to bypass executable search from PATH
    old_command_to_full_path = taskgraph.modules.command_to_full_path
    taskgraph.modules.command_to_full_path = ["executable"]

    # Initialize task
    taskgraph.modules.struct_to_task(
        "module",
        [
            {
                "name": "task",
                "executable": "executable",
                "inputs": ["inputName"],
                "optionalInputs": ["optionalInputName"]
            },
        ],
    )

    task = taskgraph.dag.get_task("task")
    nt = task.get_namedtuple()
    valuedtuple1 = nt(task_name="task", inputName="inputValue")
    assert valuedtuple1 == collections.namedtuple(
        "task",
        ["task_name", "inputName", "optionalInputName"],
    )("task", "inputValue", taskgraph.task.Task.empty_input_value)


def test_store_results():
    # Initialize command_to_full_path to bypass executable search from PATH
    old_command_to_full_path = taskgraph.modules.command_to_full_path
    taskgraph.modules.command_to_full_path = ["executable"]

    # Initialize task
    taskgraph.modules.struct_to_task(
        "module",
        [
            {
                "name": "task",
                "executable": "executable",
                "inputs": ["inputName"],
            },
        ],
    )

    # Switch terminal runnable with a Mock
    task = taskgraph.dag.get_task("task")
    task.runnable = Mock()

    # Create first valuetask
    valuetask1 = taskgraph.runner.ValueTask.create_value_task(
        name="task",
        values={
            "inputName": "inputValue",
        },
    )

    # Execute first valuetask
    result = valuetask1.run()

    # Check results
    assert result == task.runnable.return_value
    assert task.runnable.mock_calls == [
        (
            '',
            (),
            {
                "inputName": "inputValue",
            }
        )
    ]

    # Create second identical valuetask
    valuetask2 = taskgraph.runner.ValueTask.create_value_task(
        name="task",
        values={
            "inputName": "inputValue",
        },
    )

    # Execute the second valuetask
    # Execute first valuetask
    result = valuetask1.run()

    # Check results
    assert result == task.runnable.return_value

    # Especially check the mock was not run again but cached result
    # was used
    assert task.runnable.mock_calls == [
        (
            '',
            (),
            {
                "inputName": "inputValue",
            }
        )
    ]


def test_tasks_store_results():
    # Initialize command_to_full_path to bypass executable search from PATH
    old_command_to_full_path = taskgraph.modules.command_to_full_path
    taskgraph.modules.command_to_full_path = ["a", "b", "c"]

    # Initialize task
    taskgraph.modules.struct_to_task(
        "module",
        [
            {
                "name": "a",
                "executable": "a",
            },
            {
                "name": "b",
                "executable": "b",
                "inputs": ['a'],
            },
            {
                "name": "c",
                "executable": "c",
                "inputs": ['a'],
            },
        ],
    )
    # Switch terminal runnable with a Mock for all tasks
    task_a = taskgraph.dag.get_task("a")
    task_a.runnable = Mock()

    task_b = taskgraph.dag.get_task("b")
    task_b.runnable = Mock()

    task_c = taskgraph.dag.get_task("c")
    task_c.runnable = Mock()

    # Create ValueTask and execute b and it's dependency a
    valuetask_b = taskgraph.runner.ValueTask.create_value_task(name="b")
    result_b = valuetask_b.run()

    # Check task b runnable is returning correct result
    assert result_b == task_b.runnable.return_value

    # Check task a was called
    assert task_a.runnable.mock_calls == [
        (
            '',
            (),
            {}
        )
    ]

    # Check task b was called with input a as parameter
    assert task_b.runnable.mock_calls == [
        (
            '',
            (),
            {"a": task_a.runnable.return_value}
        )
    ]

    # Create ValueTask and execute c but it's dependency a will not be executed
    valuetask_c = taskgraph.runner.ValueTask.create_value_task(name="c")
    result_c = valuetask_c.run()

    # Check task a was not called again
    assert task_a.runnable.mock_calls == [
        (
            '',
            (),
            {}
        )
    ]

    # Check task b was called with input a as parameter
    assert task_c.runnable.mock_calls == [
        (
            '',
            (),
            {"a": task_a.runnable.return_value}
        )
    ]


def test_task_input_module_name():
    expected_result = "result"
    runnable = Mock(return_value=expected_result)
    inputnames = ["mandatoryinput"]
    optionalinputnames = ["optionalinput"]
    task = taskgraph.task.Task(
        module="blah",
        name="testtask",
        runnable=runnable,
        inputs=inputnames,
        optionalInputs=optionalinputnames,
        defaultInput=inputnames[0],
    )
    input_values = {
        "mandatoryinput": "mandatoryinputvalue",
    }
    result = task.run(input_values)
    assert result == expected_result
    assert runnable.mock_calls == [
        (
            '',
            (),
            input_values,
        ),
    ]