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

import nurmi.dag
import nurmi.step

def test_steps():
    bookkeeper = nurmi.dag.StepBookkeeper()
    C = nurmi.step.step(target="C", inputs=["A", "B"])
    bookkeeper.add(C)

    F = nurmi.step.step(target="F", inputs=["D", "E"])
    bookkeeper.add(F)
    H = nurmi.step.step(target="H", inputs=["C", "F", "G"])
    bookkeeper.add(H)

    assert bookkeeper.get_step("C", "A", "B") == C
    assert bookkeeper.get_step("C", "A") is None
    assert bookkeeper.get_step("C", "B") is None
    assert bookkeeper.get_step("A") is None
    assert bookkeeper.get_step("F", "D", "E") == F
    assert bookkeeper.get_step("H", "C", "F", "G") == H

    inputs = bookkeeper.get_inputs_to_target("H")
    assert inputs.index("C") > inputs.index("A")
    assert inputs.index("C") > inputs.index("B")
    assert inputs.index("F") > inputs.index("D")
    assert inputs.index("F") > inputs.index("E")
    assert inputs.index("H") > inputs.index("C")
    assert inputs.index("H") > inputs.index("F")
    assert inputs.index("H") > inputs.index("G")


# nurmi.dag.Path.add_step(C)
# nurmi.dag.Path.add_step(F)
# nurmi.dag.Path.add_step(H)

# p = nurmi.dag.Path(C)
# p.add_path(H)
#
#
#
# assert bottom_to_top.final_target == "C"
# assert bottom_to_top.required_inputs == {"A", "B"}
# assert bottom_to_top.calculated_inputs == set()
# assert bottom_to_top.steps == [C]
#
# bottom_to_top.add_step(F)

