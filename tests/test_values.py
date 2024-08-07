import taskgraph.dag
import taskgraph.results
import taskgraph.values
import taskgraph.task


from unittest.mock import *

def test_fetch_value_set_value():
    # Test fetching set value
    pass

def test_fetch_value_set_result():
    # Test fetching value which is cached result of executed task
    pass

def test_fetch_value():
    # Test fetching value which is not in cache but
    # result of a task which will be executed

    runnable = Mock()
    runnable.return_value = "testresult"
    task = taskgraph.task.Task(
        name="task",
        runnable=runnable,
        module="module",
        inputs=["environment_variable", "commandline_variable"],
    )
    values = {
        "environment_variable": "environment_value",
        "commandline_variable": "commandline_value",
    }
    taskgraph.values.add_value_names(list(values.keys()))
    taskgraph.values.set_environment_values(
        {
            "environment_variable": values["environment_variable"],
        },
    )
    taskgraph.values.set_command_line_value(
        "commandline_variable",
        values["commandline_variable"],
    )
    assert taskgraph.values.fetch_value("environment_variable") == values["environment_variable"]
    assert taskgraph.values.fetch_value("commandline_variable") == values["commandline_variable"]
    assert taskgraph.values.fetch_value("task") == runnable.return_value
    assert runnable.mock_calls == [
        (
            "",
            (),
            values,
        )
    ]
    assert taskgraph.values.fetch_value("task") == runnable.return_value
    taskgraph.results.reset()
    taskgraph.dag.reset()
    taskgraph.values.reset()


