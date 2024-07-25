from unittest.mock import *

import taskgraph.results
import taskgraph.task
import taskgraph.values


def test_fetch_value_dependency():
    # Test fetching value which is not in cache but
    # result of a task which will be executed
    taskgraph.results.reset()
    taskgraph.dag.reset()
    runnable_b = Mock()
    runnable_b.return_value = 'result_b'
    task_b = taskgraph.task.Task(
        name="b",
        runnable=runnable_b,
        module="module",
        inputs=["a"],
    )

    runnable_c = Mock()
    runnable_c.return_value = 'result_c'
    task_c = taskgraph.task.Task(
        name="c",
        runnable=runnable_c,
        module="module",
        inputs=["b"],
    )
    valuestack = taskgraph.values.ValueStack(['a', 'b', 'c'])
    valuestack.set_command_line_value('a',"value_a")

    result = valuestack.fetch_value('c')
    assert result == "result_c"
    assert runnable_c.mock_calls == [
        (
            '',
            (),
            {'b': "result_b"},
        )
    ]
    assert runnable_b.mock_calls == [
        (
            '',
            (),
            {'a': "value_a"},
        )
    ]
    assert taskgraph.results.results_in_order[0]["finish_timestamp"] < \
        taskgraph.results.results_in_order[1]["finish_timestamp"]
    del(taskgraph.results.results_in_order[0]["finish_timestamp"])
    del(taskgraph.results.results_in_order[1]["finish_timestamp"])
    assert taskgraph.results.results_in_order == [
        {
            'result': 'result_b',
            'task': task_b,
            'values': {
                'a': 'value_a',
            }
        },
        {
            'result': 'result_c',
            'task': task_c,
            'values': {
                'b': 'result_b',
            }
        }
    ]
    taskgraph.results.reset()
    taskgraph.dag.reset()