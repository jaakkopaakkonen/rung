import pytest
import time

from unittest.mock import Mock

import taskgraph.task
import taskgraph.runner

def test_taskwithinputs_complete_optional():
    runnable = Mock()
    inputs = ["beta", "gamma"]
    optionalInputs = ["delta", "epsilon"]
    taskname = "task"
    task = taskgraph.task.Task(
        target=taskname,
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
    task_with_inputs = taskgraph.runner.TaskWithInputs(taskname, values)
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
    taskname = "task"
    task = taskgraph.task.Task(
        target=taskname,
        runnable=runnable,
        inputs=inputs,
        optionalInputs=optionalInputs,
    )
    values = {
        "beta": "b",
        "gamma": "g",
        "delta": "d",
    }
    task_with_inputs = taskgraph.runner.TaskWithInputs(taskname, values)
    assert task_with_inputs.inputs == values
    result = task_with_inputs.run()
    assert result == runnable.return_value
    assert runnable.mock_calls == [
        (
            "",
            (),
            values,
        ),
    ]


def test_taskwithinputs_no_optional():
    runnable = Mock()
    inputs = ["beta", "gamma"]
    optionalInputs = ["delta", "epsilon"]
    taskname = "task"
    task = taskgraph.task.Task(
        target=taskname,
        runnable=runnable,
        inputs=inputs,
        optionalInputs=optionalInputs,
    )
    values = {
        "beta": "b",
        "gamma": "g",
    }
    task_with_inputs = taskgraph.runner.TaskWithInputs(taskname, values)
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


def test_two_taskswithinputs_happy():
    taskname = "alpha"
    inputs = ["beta", "gamma"]
    runnable_alpha = Mock(
        side_effect=lambda beta, gamma: {
            "beta": beta,
            "gamma": gamma,
            "time": time.time(),
        }
    )
    task_alpha = taskgraph.task.Task(
        target=taskname,
        runnable=runnable_alpha,
        inputs=inputs,
    )
    taskname = "beta"
    inputs = ["delta", "epsilon"]
    runnable_beta = Mock(
        side_effect=lambda delta, epsilon: {
            "delta": delta,
            "epsilon": epsilon,
            "time":time.time()
        },
    )
    task_beta = taskgraph.task.Task(
        target=taskname,
        runnable = runnable_beta,
        inputs=inputs,
    )
    run_inputs = {
        "delta": "delta",
        "gamma": "gamma",
        "epsilon": "epsilon",
    }
    taskwithinputs_alpha = taskgraph.runner.TaskWithInputs(
        target="alpha",
        inputs=run_inputs,
    )
    result = taskwithinputs_alpha.run()
    # Depedency beta was executed before maintask alpha
    assert result["time"] > result["beta"]["time"]
    del(result["time"])
    del(result["beta"]["time"])
    assert result == {
        "beta": {
            "delta": "delta",
            "epsilon": "epsilon",
        },
        "gamma": "gamma",
    }


def test_two_taskswithinputs_with_parent_values_happy():
    # TODO add values
    taskname = "alpha"
    inputs = ["beta", "gamma"]
    runnable_alpha = Mock(
        side_effect=lambda beta, gamma: {
            "beta": beta,
            "gamma": gamma,
            "time": time.time(),
        }
    )
    task_alpha = taskgraph.task.Task(
        target=taskname,
        runnable=runnable_alpha,
        inputs=inputs,
    )
    taskname = "beta"
    inputs = ["delta", "epsilon"]
    runnable_beta = Mock(
        side_effect=lambda delta, epsilon: {
            "delta": delta,
            "epsilon": epsilon,
            "time":time.time()
        },
    )
    task_beta = taskgraph.task.Task(
        target=taskname,
        runnable = runnable_beta,
        inputs=inputs,
    )
    run_inputs = {
        "delta": "delta",
        "gamma": "gamma",
        "epsilon": "epsilon",
    }
    taskwithinputs_alpha = taskgraph.runner.TaskWithInputs(
        target="alpha",
        inputs=run_inputs,
    )
    result = taskwithinputs_alpha.run()
    # Depedency beta was executed before maintask alpha
    assert result["time"] > result["beta"]["time"]
    del(result["time"])
    del(result["beta"]["time"])
    assert result == {
        "beta": {
            "delta": "delta",
            "epsilon": "epsilon",
        },
        "gamma": "gamma",
    }


def test_two_taskswithinputs_with_child_values_happy():
    # Add values
    taskname = "alpha"
    inputs = ["beta", "gamma"]
    runnable_alpha = Mock(
        side_effect=lambda beta, gamma: {
            "beta": beta,
            "gamma": gamma,
            "time": time.time(),
        }
    )
    task_alpha = taskgraph.task.Task(
        target=taskname,
        runnable=runnable_alpha,
        inputs=inputs,
    )
    taskname = "beta"
    inputs = ["delta", "epsilon"]
    runnable_beta = Mock(
        side_effect=lambda delta, epsilon: {
            "delta": delta,
            "epsilon": epsilon,
            "time":time.time()
        },
    )
    task_beta = taskgraph.task.Task(
        target=taskname,
        runnable = runnable_beta,
        inputs=inputs,
    )
    run_inputs = {
        "delta": "delta",
        "gamma": "gamma",
        "epsilon": "epsilon",
    }
    taskwithinputs_alpha = taskgraph.runner.TaskWithInputs(
        target="alpha",
        inputs=run_inputs,
    )
    result = taskwithinputs_alpha.run()
    # Depedency beta was executed before maintask alpha
    assert result["time"] > result["beta"]["time"]
    del(result["time"])
    del(result["beta"]["time"])
    assert result == {
        "beta": {
            "delta": "delta",
            "epsilon": "epsilon",
        },
        "gamma": "gamma",
    }