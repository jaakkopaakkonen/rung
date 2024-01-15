import os
import pytest
import sys

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


@pytest.mark.skip
def test_task_with_command_line_parts():
    task_structure = {
        "target": "commit",
        "executable": "echo",
        "command_line_arguments": [
            "echo git commit --dry-run",
            "--file={commit_message_file}",
            "--message=\"{commit_message}\"",
        ],
        "optional_input_names": [
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
        target="testtask",
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