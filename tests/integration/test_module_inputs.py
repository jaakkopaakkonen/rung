import taskgraph.valuestack
import taskgraph.dag
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
    valuestack = taskgraph.valuestack.ValueStack(
        taskgraph.inputs.get_all_input_names(),
    )
    valuestack.set_environment_values(
        {
            "moduleinputA": "valueA",
            "module_inputB": "valueB",
        }
    )
    valuetask = taskgraph.runner.ValueTask.create_value_task(
        name="task",
        values=valuestack.get_values(),
    )
    result = valuetask.run()
    assert result


