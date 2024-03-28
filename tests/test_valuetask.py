import copy
import pytest
import time
import unittest.mock

import taskgraph.dag
import taskgraph.task
import taskgraph.runner


def test_valuetask_complete_optional():
    runnable = unittest.mock.Mock()
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
    task_with_inputs = taskgraph.runner.ValueTask(taskname, values)
    assert task_with_inputs.values == values
    result = task_with_inputs.run()
    assert result == runnable.return_value
    assert runnable.mock_calls == [
        (
            "",
            (),
            values,
        )
    ]


def test_valuetask_partial_optional():
    runnable = unittest.mock.Mock()
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
    valuetask = taskgraph.runner.ValueTask(taskname, values)
    assert valuetask.values == values
    result = valuetask.run()
    assert result == runnable.return_value
    assert runnable.mock_calls == [
        (
            "",
            (),
            values,
        ),
    ]


def test_valuetask_no_optional():
    runnable = unittest.mock.Mock()
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
    valuetask = taskgraph.runner.ValueTask(taskname, values)
    assert valuetask.values == values
    result = valuetask.run()
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
    runnable_alpha = unittest.mock.Mock(
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
    runnable_beta = unittest.mock.Mock(
        side_effect=lambda delta, epsilon: {
            "delta": delta,
            "epsilon": epsilon,
            "time": time.time()
        },
    )
    task_beta = taskgraph.task.Task(
        target=taskname,
        runnable=runnable_beta,
        inputs=inputs,
    )
    run_inputs = {
        "delta": "delta",
        "gamma": "gamma",
        "epsilon": "epsilon",
    }
    valuetask_alpha = taskgraph.runner.ValueTask(
        target="alpha",
        values=run_inputs,
    )
    result = valuetask_alpha.run()
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
    runnable_alpha = unittest.mock.Mock(
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
    runnable_beta = unittest.mock.Mock(
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
    valuetask_alpha = taskgraph.runner.ValueTask(
        target="alpha",
        values=run_inputs,
    )
    result = valuetask_alpha.run()
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
    runnable_car = unittest.mock.Mock(
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
    runnable_beta = unittest.mock.Mock(
        side_effect=lambda carburetor, engine_block: {
            "carburetor": carburetor,
            "engine_block": engine_block,
            "time":time.time(),
        },
    )
    task_beta = taskgraph.task.Task(
        target=taskname,
        runnable = runnable_beta,
        inputs=inputs,
    )
    run_values = {
        "carburetor": "bendix",
        "tyres": "michelin",
        "engine_block": "dynacast",
    }
    valuetask_car = taskgraph.runner.ValueTask(
        target="car",
        values=run_values,
    )
    result = valuetask_car.run()
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
    taskgraph.dag.reset()


def test_task_with_values():
    taskname = "car"
    inputs = ["engine", "tyres"]
    runnable_car = unittest.mock.Mock(
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
    # assert child_task.run({"gears": "four"}) == "transmission has four gears"

    car_valuetask = taskgraph.runner.ValueTask(
        target=taskname,
        values={
            "engine": "volvo",
            "tyres": "michelin",
            "gears": "four",
        },
    )
    result = car_valuetask.run()
    print(result)
    taskgraph.dag.reset()


def test_inline_task_in_values_one_match():
    import taskgraph.main
    testtask = taskgraph.task.Task(
        target="testtask",
        inputs=["searchPattern"],
        values={
            "pattern": "alpha",
            "text": "{alpha}\nbeta\ngamma",
        },
    )
    testtaskwi = taskgraph.runner.ValueTask(
        target="testtask",
        values={"alpha": "balpha"},
    )
    result = testtaskwi.run()
    assert result == "balpha"
    taskgraph.dag.reset()


def test_taskwihinputs_deepcopy():
    readfile_mock = unittest.mock.Mock(
        side_effect=lambda file: "halipatsuippa",
    )
    readfile_task = taskgraph.task.Task(
        target="readfile",
        runnable=readfile_mock,
        inputs=["file"],
        defaultInput="file",
    )
    build_id_task = taskgraph.task.Task(
        target="build_id",
        inputs=["readfile"],
        values={
            "file": "file-{REVISION}-{VARIANT}-{RELEASE}",
        },
    )
    build_id_valuetask = taskgraph.runner.ValueTask(
        target="build_id",
        values={
            "REVISION": "dunfell",
            "VARIANT": "mp",
            "RELEASE": "master",
        },
    )
    copy_of_build_id_valuetask = copy.deepcopy(build_id_valuetask)
    assert build_id_valuetask == copy_of_build_id_valuetask
    taskgraph.dag.reset()


def test_inline_task_in_values_two_matches():
    # Set up tasks
    readfile_mock = unittest.mock.Mock(
        side_effect=lambda file: "halipatsuippa",
    )
    readfile_task = taskgraph.task.Task(
        target="readfile",
        runnable=readfile_mock,
        inputs=["file"],
        defaultInput="file",
    )
    build_id_task = taskgraph.task.Task(
        target="build_id",
        inputs=["readfile"],
        values={
            "file": "file-{REVISION}-{VARIANT}-{RELEASE}",
        },
    )
    build_id_valuetask = taskgraph.runner.ValueTask(
        target="build_id",
        values={
            "REVISION": "dunfell",
            "VARIANT": "mp",
            "RELEASE": "master",
        },
    )

    # Check valuetask is correct
    file_valuetask = taskgraph.runner.ValueTask(
        target="file-{REVISION}-{VARIANT}-{RELEASE}",
        values={
            "REVISION": "dunfell",
            "VARIANT": "mp",
            "RELEASE": "master",
        },
    )
    readfile_valuetask = taskgraph.runner.ValueTask(
        target="readfile",
        values={
            "file": file_valuetask,
        },
    )
    check_build_id_task_with_inputs = copy.deepcopy(build_id_valuetask)
    check_build_id_task_with_inputs.inputs = {
        "readfile": readfile_valuetask,
    }
    assert build_id_valuetask == check_build_id_task_with_inputs

    result = build_id_valuetask.run()
    assert readfile_mock.mock_calls == [
        (
            '',
            (),
            {"file": "file-dunfell-mp-master"},
        ),
    ]
    assert result == "halipatsuippa"
    taskgraph.dag.reset()


def test_valuetask_missing_value():
    test_task = taskgraph.task.Task(
        target="testtask",
        inputs=["anothertask"],
    )
    with pytest.raises(taskgraph.runner.MissingInputException) as mie:
        taskgraph.runner.ValueTask(
            target="testtask",
            values={},
        )
    taskgraph.dag.reset()
