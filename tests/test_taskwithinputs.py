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
    taskname = "car"
    inputs = ["engine", "tyres"]
    runnable_car = Mock(
        side_effect=lambda engine, tyres: {
            "engine": engine,
            "tyres": tyres,
            "time": time.time(),
        }
    )
    task_car = taskgraph.task.Task(
        target=taskname,
        runnable=runnable_car,
        inputs=inputs,
    )
    taskname = "engine"
    inputs = ["carburetor", "engine_block"]
    runnable_beta = Mock(
        side_effect=lambda carburetor, engine_block: {
            "carburetor": carburetor,
            "engine_block": engine_block,
            "time":time.time()
        },
    )
    task_beta = taskgraph.task.Task(
        target=taskname,
        runnable = runnable_beta,
        inputs=inputs,
    )
    run_inputs = {
        "carburetor": "bendix",
        "tyres": "michelin",
        "engine_block": "dynacast",
    }
    taskwithinputs_car = taskgraph.runner.TaskWithInputs(
        target="car",
        inputs=run_inputs,
    )
    result = taskwithinputs_car.run()
    # Depedency engine was executed before maintask car
    assert result["time"] > result["engine"]["time"]
    del(result["time"])
    del(result["engine"]["time"])
    assert result == {
        "engine": {
            "carburetor": "bendix",
            "engine_block": "dynacast",
        },
        "tyres": "michelin",
    }


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
    car_task = taskgraph.task.Task(
        target=taskname,
        runnable=runnable_car,
        inputs=inputs,
        providedValues=values,
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
    # assert child_task.run({"gears": "four"}) == "transmission has four gears"

    car_taskwithinputs = taskgraph.runner.TaskWithInputs(
        target=taskname,
        inputs={
            "engine": "volvo",
            "tyres": "michelin",
            "gears": "four",
        },
    )
    result = car_taskwithinputs.run()
    print(result)
