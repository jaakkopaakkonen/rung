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


def test_task_with_command_line_parts():
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
    taskgraph.modules.command_to_full_path = {"echo": "/usr/bin/echo"}
    taskgraph.modules.struct_to_task(task_structure)
    task = taskgraph.dag.get_task("commit")
    result =  task.run({"commit_message_file": "commit.md"})
    assert result == "echo git commit --dry-run --file=commit.md"


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
    assert child_task.input_names == ["gears"]
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
    valuetask = taskgraph.runner.ValueTask.createValueTask(
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
                "command": "ssh www.google.com sudo supervisorctl tail -f searchengine",
                "title": "www.google.com: supervisorctl tail -f searchengine",
            },
        ),
    ]
    # Revert original command_to_full_path
    taskgraph.modules.command_to_full_path = old_command_to_full_path
