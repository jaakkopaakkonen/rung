from unittest.mock import *

import taskgraph.modules
import taskgraph.task
import taskgraph.results


def test_consecutivetask_simple():
    runnable_a = Mock(return_value="result_a")
    task_a = taskgraph.task.Task(
        name="a",
        runnable=runnable_a,
    )
    runnable_b = Mock(return_value="result_b")
    task_b = taskgraph.task.Task(
        name="b",
        runnable=runnable_b,
    )
    runnable_c = Mock(return_value="result_c")
    task_c = taskgraph.task.Task(
        name="c",
        runnable=runnable_c,
    )
    runnable_d = Mock(return_value="result_d")
    task_d = taskgraph.task.Task(
        name="d",
        runnable=runnable_d,
    )
    consecutive_task = taskgraph.task.ConsecutiveTask.create_consecutive_tasks(
        ['a', 'b', 'c', 'd'],
    )
    consecutive_task.run()
    assert runnable_d.mock_calls == [
        (
            '',
            (),
            {},
        )
    ]
    assert runnable_c.mock_calls == [
        (
            '',
            (),
            {},
        )
    ]
    assert runnable_b.mock_calls == [
        (
            '',
            (),
            {},
        )
    ]
    assert runnable_a.mock_calls == [
        (
            '',
            (),
            {},
        )
    ]
    results = taskgraph.results.results_in_order
    assert results[0]["finish_timestamp"] < results[1]["finish_timestamp"] < results[2]["finish_timestamp"] < results[3]["finish_timestamp"]
    del(results[0]["finish_timestamp"])
    del(results[1]["finish_timestamp"])
    del(results[2]["finish_timestamp"])
    del(results[3]["finish_timestamp"])
    assert results == [
        {
            "values": {},
            "task": task_a,
            "result": "result_a",
        },
        {
            "values": {},
            "task": task_b,
            "result": "result_b",
        },
        {
            "values": {},
            "task": task_c,
            "result": "result_c",
        },
        {
            "values": {},
            "task": task_d,
            "result": "result_d",
        },
    ]
    taskgraph.dag.reset()
    taskgraph.results.reset()
    taskgraph.values.reset()


def test_consecutivetask_dependencies():
    # a┐ a┐ d┐
    #  b  c  e
    runnable_a = Mock(return_value="result_a")
    task_a = taskgraph.task.Task(
        name="a",
        runnable=runnable_a,
    )
    runnable_b = Mock(return_value="result_b")
    task_b = taskgraph.task.Task(
        name="b",
        runnable=runnable_b,
        inputs=['a']
    )
    runnable_c = Mock(return_value="result_c")
    task_c = taskgraph.task.Task(
        name="c",
        runnable=runnable_c,
        inputs=['a']
    )
    runnable_d = Mock(return_value="result_d")
    task_d = taskgraph.task.Task(
        name="d",
        runnable=runnable_d,
    )
    runnable_e = Mock(return_value="result_e")
    task_e = taskgraph.task.Task(
        name="e",
        runnable=runnable_e,
        inputs=['d']
    )
    consecutive_task = taskgraph.task.ConsecutiveTask.create_consecutive_tasks(
        ['b', 'c', 'e'],
    )
    consecutive_task.run()
    assert runnable_a.mock_calls == [
        (
            '',
            (),
            {},
        )
    ]
    assert runnable_c.mock_calls == [
        (
            '',
            (),
            {'a': "result_a"},
        )
    ]
    assert runnable_b.mock_calls == [
        (
            '',
            (),
            {"a": "result_a"},
        )
    ]
    assert runnable_c.mock_calls == [
        (
            '',
            (),
            {'a': "result_a"},
        )
    ]
    results = taskgraph.results.results_in_order
    assert results[0]["finish_timestamp"] < results[1]["finish_timestamp"] < results[2]["finish_timestamp"] < results[3]["finish_timestamp"]
    del(results[0]["finish_timestamp"])
    del(results[1]["finish_timestamp"])
    del(results[2]["finish_timestamp"])
    del(results[3]["finish_timestamp"])
    del(results[4]["finish_timestamp"])
    assert results == [
        {
            "values": {},
            "task": task_a,
            "result": "result_a",
        },
        {
            "values": {
                'a': "result_a",
            },
            "task": task_b,
            "result": "result_b",
        },
        {
            "values": {
                'a': "result_a",
            },
            "task": task_c,
            "result": "result_c",
        },
        {
            "values": {},
            "task": task_d,
            "result": "result_d",
        },
        {
            "values": {'d': "result_d"},
            "task": task_e,
            "result": "result_e",
        },
    ]
    taskgraph.dag.reset()
    taskgraph.results.reset()


def test_append():
    # a─c─d┐
     #  e──f

    # Set up runnables and tasks
    runnable_a = Mock()
    task_a = taskgraph.task.Task(
        name='a',
        runnable=runnable_a,
    )
    runnable_d = Mock(return_value="result_d")
    task_d = taskgraph.task.Task(
        name='d',
        runnable=runnable_d,
    )
    runnable_e = Mock(return_value="result_e")
    task_e = taskgraph.task.Task(
        name='e',
        runnable=runnable_e,
    )
    runnable_f = Mock(return_value="result_f")
    task_f = taskgraph.task.Task(
        name='f',
        runnable=runnable_f,
    )

    # Set up consecutivetasks and a condition
    a = taskgraph.task.ConsecutiveTask(task_name='a')
    c = taskgraph.task.Condition(
        input_names='a',
        evaluator=lambda a:a,
    )
    d = taskgraph.task.ConsecutiveTask(task_name='d')
    e = taskgraph.task.ConsecutiveTask(task_name='e')
    f = taskgraph.task.ConsecutiveTask(task_name='f')

    # Build consecutivetask graph and
    # assert returned consecutivetasks from append method
    assert a.append(next_consecutive_task=c) == c
    assert c.append(next_consecutive_task=d, result=True) == d
    assert c.append(next_consecutive_task=e, result=False) == e
    assert c.append(next_consecutive_task=f) == f

    # Check consecutivetask graph
    assert a.next_consecutive_task == c
    assert c.condition_map == {True: d, False: e}
    assert d.next_consecutive_task == f
    assert e.next_consecutive_task == f

    # Run graph with a=True branch
    runnable_a.return_value = True
    result = a.run()

    # Check results
    assert result == "result_f"
    results = taskgraph.results.results_in_order
    assert results[0]["finish_timestamp"] < results[1]["finish_timestamp"] < results[2]["finish_timestamp"]
    del(results[0]["finish_timestamp"])
    del(results[1]["finish_timestamp"])
    del(results[2]["finish_timestamp"])
    assert results == [
        {
            "values": {},
            "task": task_a,
            "result": True,
        },
        {
            "values": {},
            "task": task_d,
            "result": "result_d",
        },
        {
            "values": {},
            "task": task_f,
            "result": "result_f",
        },
    ]
    # Reset results
    taskgraph.results.reset()

    # Run same graph again with a=False branch
    runnable_a.return_value = False
    result = a.run()

    # Check results
    assert result == "result_f"
    results = taskgraph.results.results_in_order
    assert results[0]["finish_timestamp"] < results[1]["finish_timestamp"] < results[2]["finish_timestamp"]
    del(results[0]["finish_timestamp"])
    del(results[1]["finish_timestamp"])
    del(results[2]["finish_timestamp"])
    assert results == [
        {
            "values": {},
            "task": task_a,
            "result": False,
        },
        {
            "values": {},
            "task": task_e,
            "result": "result_e",
        },
        {
            "values": {},
            "task": task_f,
            "result": "result_f",
        },
    ]