import taskgraph.values
import taskgraph.dag
import taskgraph.results
import taskgraph.runner
import taskgraph.task

from unittest.mock import *


def test_task_input_module_name():
    runnable = Mock()
    task = taskgraph.task.Task(
        name="task",
        runnable=runnable,
        inputs=["inputA", "inputB"],
        defaultInput="inputA",
        module="module",
    )
    taskgraph.values.add_value_names(
        taskgraph.inputs.get_all_input_names(),
    )
    taskgraph.values.set_environment_values(
        {
            "moduleinputA": "valueA",
            "module_inputB": "valueB",
        }
    )
    valuetask = taskgraph.runner.ValueTask.create_value_task(
        name="task",
        values=taskgraph.values.get_values(),
    )
    result = valuetask.run()
    assert result
    taskgraph.values.reset()
    taskgraph.results.reset()
    taskgraph.dag.reset()
