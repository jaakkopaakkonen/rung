import taskgraph.dag
import taskgraph.matrix
import taskgraph.modules
import taskgraph.task
import taskgraph.util

from unittest.mock import *


@patch("taskgraph.modules.command_to_full_path", ['a', 'b', 'c'])
def test_get_asciitree():
    taskgraph.modules.struct_to_task(
        "module",
        [
            {
                "name": "a",
                "executable": "a",
            },
            {
                "name": "b",
                "executable": "b",
                "inputs": ['a'],
            },
            {
                "name": "c",
                "executable": "c",
                "inputs": ['a'],
            },
        ],
    )
    task = taskgraph.dag.get_task("b")
    tree = taskgraph.util.get_asciitree(task)
    asciitree = tree.get_tree()
    print(asciitree)
    assert asciitree == "a─b"