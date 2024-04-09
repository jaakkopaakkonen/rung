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
import taskgraph.runner


def test_get_results():
    # Initialize command_to_full_path to bypass executable search from PATH
    old_command_to_full_path = taskgraph.modules.command_to_full_path
    taskgraph.modules.command_to_full_path = ["executable"]

    # Initialize task
    taskgraph.modules.struct_to_task(
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

    # Get_results returns none when inputs mismatch
    assert taskgraph.results.get_results(task) == None

    # Get results when nothing has been stored in the first place
    assert taskgraph.results.get_results(
        task=task,
        values={"inputName": "inputValue"},
    ) == None

    # Store a result
    result = Mock()
    before = time.time()
    taskgraph.results.add(task, {"inputName": "inputValue"}, result)
    after = time.time()

    # Try to get result with different values
    assert taskgraph.results.get_results(
        task=task,
        values={"inputName": "otherInputValue"},
    ) == None

    # Try to get result with correct value
    return_value = taskgraph.results.get_results(
        task=task,
        values={"inputName": "inputValue"},
    )
    assert before < return_value["finish_timestamp"] < after
    assert return_value["values"] == {"inputName": "inputValue"}
    assert return_value["result"] == result

    # Create task with same input names but different name
    taskgraph.modules.struct_to_task(
        [
            {
                "name": "other_task",
                "executable": "executable",
                "inputs": ["inputName"],
                "optionalInputs": ["optionalInputName"]
            },
        ],
    )
    other_task = taskgraph.dag.get_task("task")
    taskgraph.results.get_results(
        task=other_task,
        values={"inputName": "inputValue"}
    ) == None

    # Check once again original value is returned
    return_value = taskgraph.results.get_results(
        task=task,
        values={"inputName": "inputValue"},
    )
    assert before < return_value["finish_timestamp"] < after
    assert return_value["values"] == {"inputName": "inputValue"}
    assert return_value["result"] == result
