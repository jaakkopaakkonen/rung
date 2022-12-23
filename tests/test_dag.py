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

import taskgraph.dag
import taskgraph.task

def test_tasks():
    bookkeeper = taskgraph.dag.TaskBookkeeper()
    C = taskgraph.task.Task(name="C", inputs=["A", "B"])
    bookkeeper.add(C)

    F = taskgraph.task.Task(name="F", inputs=["D", "E"])
    bookkeeper.add(F)
    H = taskgraph.task.Task(name="H", inputs=["C", "F", "G"])
    bookkeeper.add(H)

    assert bookkeeper.get_task("C", "A", "B") == C
    assert bookkeeper.get_task("C", "A") is None
    assert bookkeeper.get_task("C", "B") is None
    assert bookkeeper.get_task("A") is None
    assert bookkeeper.get_task("F", "D", "E") == F
    assert bookkeeper.get_task("H", "C", "F", "G") == H

    assert bookkeeper.final_tasks().pop() == "H"

    inputs = bookkeeper.get_inputs_to_task("H")
    assert inputs.index("C") > inputs.index("A")
    assert inputs.index("C") > inputs.index("B")
    assert inputs.index("F") > inputs.index("D")
    assert inputs.index("F") > inputs.index("E")
    assert inputs.index("H") > inputs.index("C")
    assert inputs.index("H") > inputs.index("F")
    assert inputs.index("H") > inputs.index("G")
