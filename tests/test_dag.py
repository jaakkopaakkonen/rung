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

import rung.dag
import rung.step

def test_steps():
    bookkeeper = rung.dag.StepBookkeeper()
    C = rung.step.step(target="C", inputs=["A", "B"])
    bookkeeper.add(C)

    F = rung.step.step(target="F", inputs=["D", "E"])
    bookkeeper.add(F)
    H = rung.step.step(target="H", inputs=["C", "F", "G"])
    bookkeeper.add(H)

    assert bookkeeper.get_step("C", "A", "B") == C
    assert bookkeeper.get_step("C", "A") is None
    assert bookkeeper.get_step("C", "B") is None
    assert bookkeeper.get_step("A") is None
    assert bookkeeper.get_step("F", "D", "E") == F
    assert bookkeeper.get_step("H", "C", "F", "G") == H

    assert bookkeeper.final_targets().pop() == "H"

    inputs = bookkeeper.get_inputs_to_target("H")
    assert inputs.index("C") > inputs.index("A")
    assert inputs.index("C") > inputs.index("B")
    assert inputs.index("F") > inputs.index("D")
    assert inputs.index("F") > inputs.index("E")
    assert inputs.index("H") > inputs.index("C")
    assert inputs.index("H") > inputs.index("F")
    assert inputs.index("H") > inputs.index("G")
