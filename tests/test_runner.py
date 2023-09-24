import pytest
import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.realpath(__file__),
            "../..",
        ),
    ),
)

import time

import taskgraph.results
import taskgraph.runner
import taskgraph.task
import taskgraph.valuestack


def test_python_task_return_value():
    name = "test_normal_python_task"
    return_value = "return_value"
    taskgraph.task.task(
        name=name,
        signature=(
            lambda: return_value,
        ),
    )
    before = time.time()
    result = taskgraph.runner.TaskRunner().run_task(name)
    after = time.time()
    assert name in result

    assert before < result[name]["startTime"] < result[name]["endTime"] < after
    assert result[name]["result"] == return_value


def test_shell_task_return_value():
    name = "test_normal_shell_task"
    inputs = {
        "stdout_log": "this is log",
        "return_value": 3,
    }
    taskgraph.task.task_shell_script(
        "echo {stdout_log}\n exit {return_value}",
        name,
        "stdout_log",
        "return_value",
    )
    before = time.time()
    vs = taskgraph.valuestack.ValueStack(
        list(inputs.keys())
    )
    vs.set_environment_values(inputs)
    result = taskgraph.runner.TaskRunner(vs).run_task(name)
    after = time.time()

    assert name in result
    assert before < result[name]["startTime"] < result[name]["endTime"] < after

    assert result[name]["result"][0]["command"] == "echo " + inputs["stdout_log"]
    assert result[name]["result"][0]["log"][0]["stream"] == "stdout"
    assert result[name]["result"][0]["log"][0]["data"] == inputs["stdout_log"] + "\n"

    assert result[name]["result"][1]["command"] == "exit 3"
    assert result[name]["result"][1]["return_code"] == inputs["return_value"]


def test_shell_task_extract_value():
    name = "valuetask"
    value_name = "result_value"
    taskgraph.task.task_shell_script(
        "echo yksi=one kaksi=two kolme=three",
        name,
    )
    taskgraph.results.LogValueExtractor(
        task_name=name,
        value_name=value_name,
        line_pattern="kaksi=([^ ]*)"
    )
    vs = taskgraph.valuestack.ValueStack(list(value_name))
    result = taskgraph.runner.TaskRunner(vs).run_task(name)
    assert vs.get_values() == {
        "result_value": "two",
    }
