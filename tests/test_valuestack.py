import pytest
from unittest.mock import Mock, patch
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

import taskgraph.valuestack


def test_valuestack():
    valuestack1 = taskgraph.valuestack.ValueStack(
        ["ia", "ib", "ic", "id", "ie", "if", "ig"],
    )
    valuestack1.set_environment_values(
        {
            "ia": "one",
            "ib": "hundred",
            "ic": "hundred",
            "id": "hundred",
        }
    )
    valuestack1.set_command_line_value("ib", "two")
    valuestack1.set_command_line_value("ic", "three")
    valuestack1.set_command_line_value("id", "four")

    assert valuestack1.get_values() == {
        "ia": "one",
        "ib": "two",
        "ic": "three",
        "id": "four",
    }

    valuestack2 = valuestack1.new_level_copy()

    valuestack2.set_internal_value("ie", "five")
    valuestack2.set_internal_value("if", "six")
    valuestack2.set_internal_value("ig", None)

    assert valuestack2.get_values() == {
        "ia": "one",
        "ib": "two",
        "ic": "three",
        "id": "four",
        "ie": "five",
        "if": "six",
    }
    assert valuestack1.get_values() == {
        "ia": "one",
        "ib": "two",
        "ic": "three",
        "id": "four",
        "ie": "ten",
        "ig": "seven",
    }

    valuestack3 = valuestack2.new_level_copy()
    valuestack3.set_internal_value("ig", "thousand")
    assert valuestack3.get_values() == {
        "ia": "one",
        "ib": "two",
        "ic": "three",
        "id": "four",
        "ie": "five",
        "if": "six",
        "ig": "thousand",
    }
    assert valuestack2.get_values() == {
        "ia": "one",
        "ib": "two",
        "ic": "three",
        "id": "four",
        "ie": "five",
        "if": "six",
    }
    assert valuestack1.get_values() == {
        "ia": "one",
        "ib": "two",
        "ic": "three",
        "id": "four",
        "ie": "ten",
        "ig": "seven",
    }

    assert valuestack1.is_valuename("ia") is True
    assert valuestack1.is_valuename("blah") is False
    assert valuestack1.is_valuename("blih") is False
