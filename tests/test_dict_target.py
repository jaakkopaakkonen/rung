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

from nurmi.step import step
import nurmi.values


def test_dict_input():
    c_dict = {
        "d": 4,
        "e": 5,
    }

    def c_impl(a, b):
        return c_dict

    vr = nurmi.values.ValueRunner()
    vr.read_command_line("a", 1)
    vr.read_command_line("b", 2)
    step(
        target="c",
        signature=(c_impl, "a", "b"),
        inputs=["a", "b"],
    )

    def f_impl(g):
        return "g"

    step(
        target="f",
        signature=(f_impl, "c.a"),
        inputs=["c.a"],
    )

    value = vr.run_target("f")
    print(value)
