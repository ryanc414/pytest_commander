"""Unit tests for runner module."""
import json
import os
from unittest import mock

import pytest

from pytest_web_ui import runner
from pytest_web_ui import result_tree

EXAMPLES_DIR = os.path.relpath(
    os.path.join(os.path.dirname(__file__), os.pardir, "pytest_examples")
)


@pytest.fixture
def pyrunner():
    socketio = mock.MagicMock()
    return runner.PyTestRunner(EXAMPLES_DIR, socketio)


def test_init(pyrunner):
    """
    Test initialising the PyTestRunner. Ensures that the expected result tree skeleton
    is built.
    """
    schema = result_tree.BranchNodeSchema()
    serialized = schema.dump(pyrunner.result_tree)

    json_filepath = os.path.join(
        os.path.dirname(__file__), os.pardir, "test_data", "result_tree_skeleton.json"
    )

    with open(json_filepath) as f:
        expected_serialization = json.load(f)

    assert serialized == expected_serialization


def test_run_tests(pyrunner):
    """
    Test running tests from a single module.
    """
    pyrunner._run_test("pytest_examples/test_a.py")
    assert pyrunner._socketio.emit.call_count == 5

    for test_id in (
        "test_one",
        "test_two",
        "TestSuite::test_alpha",
        "TestSuite::test_beta",
    ):
        nodeid = f"pytest_examples/test_a.py::{test_id}"
        node = pyrunner._node_index[nodeid]
        assert node.status in (
            result_tree.TestState.PASSED,
            result_tree.TestState.FAILED,
        )
        if node.status == result_tree.TestState.FAILED:
            assert node.longrepr

    node = pyrunner._node_index["pytest_examples/test_a.py"]
    assert node.status == result_tree.TestState.FAILED
