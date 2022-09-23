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

import nurmi.valuerunner
import nurmi.valuestack
import nurmi.dag


@patch(
    target="nurmi.dag.run_target_with_values",
    new_callable=Mock
)
def test_run_complex_object(run_target_with_values):
    run_target_with_values.return_value = "h"
    vs = nurmi.valuestack.ValueStack(["a", "b", "g"])

    nurmi.valuerunner.run_object(
        [
            {
                "a": {
                    "b": {"c": "d"},
                    "e": "f",
                 },
            },
            "g",
        ],
        vs
    )
    assert run_target_with_values.mock_calls == [
        ("", ("b", {"c": "d"}), {}),
        (
            "",
            (
                "a",
                {
                    "b": "h",
                    "e": "f",
                }
            ),
            {}
        ),
        ("", ("g", {"a": "h", "b": "h"}), {}),
    ]
    nurmi.valuestack.ValueStack.reset()


@patch(
    target="nurmi.dag.run_target_with_values",
    new_callable=Mock
)
def test_simple_dict(run_target_with_values):
    nurmi.valuerunner.run_object(
        {"a": {"b": "c"}},
        nurmi.valuestack.ValueStack(["a", "b"])
    )
    assert run_target_with_values.mock_calls == [
        ("", ("a", {"b": "c"}), {}),
    ]
    nurmi.valuestack.ValueStack.reset()


@patch(
    target="nurmi.dag.run_target_with_values",
    new_callable=Mock
)
def test_two_dicts_list(run_target_with_values):
    run_target_with_values.return_value = "g"
    nurmi.valuerunner.run_object(
        [
            {"a": {"b": "c"}},
            {"d": {"e": "f"}}
        ],
        nurmi.valuestack.ValueStack(["a", "b", "d", "e"])
    )
    assert run_target_with_values.mock_calls == [
        ("", ("a", {"b": "c"}), {}),
        ("", ("d", {"e": "f", "a": "g"}), {}),
    ]
    nurmi.valuestack.ValueStack.reset()


@patch(
    target="nurmi.dag.run_target_with_values",
    new_callable=Mock
)
def test_dict_inside_dict(run_target_with_values):
    run_target_with_values.return_value = "g"
    nurmi.valuerunner.run_object(
        {"a": {"b": {"c": "d"}}},
        nurmi.valuestack.ValueStack(["a", "b"])
    )
    assert run_target_with_values.mock_calls == [
        ("", ("b", {"c": "d"}), {}),
        ("", ("a", {"b": "g"}), {}),
    ]
    nurmi.valuestack.ValueStack.reset()
