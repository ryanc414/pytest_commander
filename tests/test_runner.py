"""Unit tests for runner module."""
import os

from pytest_runner import runner


def test_init():
    """
    Test initialising the PyTestRunner. Ensures that the expected result tree skeleton
    is built.
    """
    directory = os.path.join(os.path.dirname(__file__), os.pardir, "pytest_examples")
    pyrunner = runner.PyTestRunner(directory)
    expected_tree = """\
BranchNode <<Session pytest_runner exitstatus=0 testsfailed=0 testscollected=6> TestStates.INIT>
  BranchNode <<Module pytest_examples/test_a.py> TestStates.INIT>
    LeafNode <<Function test_one> TestStates.INIT>
    LeafNode <<Function test_two> TestStates.INIT>
    BranchNode <<Class TestSuite> TestStates.INIT>
      BranchNode <<Instance ()> TestStates.INIT>
        LeafNode <<Function test_alpha> TestStates.INIT>
        LeafNode <<Function test_beta> TestStates.INIT>
  BranchNode <<Module pytest_examples/test_b.py> TestStates.INIT>
    LeafNode <<Function test_one> TestStates.INIT>
    LeafNode <<Function test_two> TestStates.INIT>"""

    assert pyrunner.result_tree.pretty_format() == expected_tree


def test_run_tests():
    """
    Test running tests from a single module.
    """
    directory = os.path.join(os.path.dirname(__file__), os.pardir, "pytest_examples")
    runner_inst = runner.PyTestRunner(directory)
    runner_inst.run_tests("pytest_examples/test_a.py")

    for test_id in (
        "test_one",
        "test_two",
        "TestSuite::test_alpha",
        "TestSuite::test_beta",
    ):
        nodeid = f"pytest_examples/test_a.py::{test_id}"
        node = runner_inst._result_index[nodeid]
        assert node.report is not None
