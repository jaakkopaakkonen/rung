import pytest
from unittest.mock import Mock

import taskgraph.task
import taskgraph.runner

def test_taskwithinputs_complete_optional():
    runnable = Mock()
    inputs = ["beta", "gamma"]
    optionalInputs = ["delta", "epsilon"]
    task = taskgraph.task.Task(
        target="task",
        runnable=runnable,
        inputs=inputs,
        optionalInputs=optionalInputs,
    )
    values = {
        "beta": "b",
        "gamma": "g",
        "delta": "d",
        "epsilon": "e",
    }
    task_with_inputs = taskgraph.runner.TaskWithInputs(task, values)
    assert task_with_inputs.inputs == values
    result = task_with_inputs.run()
    assert result == runnable.return_value
    assert runnable.mock_calls == [
        (
            "",
            (),
            values,
        )
    ]


def test_taskwithinputs_partial_optional():
    runnable = Mock()
    inputs = ["beta", "gamma"]
    optionalInputs = ["delta", "epsilon"]
    task = taskgraph.task.Task(
        target="task",
        runnable=runnable,
        inputs=inputs,
        optionalInputs=optionalInputs,
    )
    values = {
        "beta": "b",
        "gamma": "g",
        "delta": "d",
    }
    task_with_inputs = taskgraph.runner.TaskWithInputs(task, values)
    assert task_with_inputs.inputs == values
    result = task_with_inputs.run()
    assert result == runnable.return_value
    assert runnable.mock_calls == [
        (
            "",
            (),
            values,
        )
    ]


def test_taskwithinputs_no_optional():
    runnable = Mock()
    inputs = ["beta", "gamma"]
    optionalInputs = ["delta", "epsilon"]
    task = taskgraph.task.Task(
        target="task",
        runnable=runnable,
        inputs=inputs,
        optionalInputs=optionalInputs,
    )
    values = {
        "beta": "b",
        "gamma": "g",
    }
    task_with_inputs = taskgraph.runner.TaskWithInputs(task, values)
    assert task_with_inputs.inputs == values
    result = task_with_inputs.run()
    assert result == runnable.return_value
    assert runnable.mock_calls == [
        (
            "",
            (),
            values,
        )
    ]
