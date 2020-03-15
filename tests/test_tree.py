"""Unit test for the result_tree package."""
import os

import pytest

from pytest_runner import result_tree


class CollectPlugin:
    """Plugin to retrieve session object after collection."""

    def __init__(self):
        self.session = None

    def pytest_collection_finish(self, session):
        self.session = session


def collect_tests(directory):
    plugin = CollectPlugin()
    pytest.main(["--collect-only", directory], plugins=[plugin])

    session = plugin.session
    return result_tree.build_from_session(session)


def test_build_from_session():
    examples_dir = os.path.join(os.path.dirname(__file__), os.pardir, "pytest_examples")
    tree = collect_tests(examples_dir)
    expected_tree = """\
BranchNode <<Session pytest_runner exitstatus=0 testsfailed=0 testscollected=6> TestStates.INIT>
  BranchNode <<Module pytest_examples/test_a.py> TestStates.INIT>
    LeafNode <<Function test_one> TestStates.INIT
    LeafNode <<Function test_two> TestStates.INIT
    BranchNode <<Class TestSuite> TestStates.INIT>
      BranchNode <<Instance ()> TestStates.INIT>
        LeafNode <<Function test_alpha> TestStates.INIT
        LeafNode <<Function test_beta> TestStates.INIT
  BranchNode <<Module pytest_examples/test_b.py> TestStates.INIT>
    LeafNode <<Function test_one> TestStates.INIT
    LeafNode <<Function test_two> TestStates.INIT"""
    assert tree.pretty_format() == expected_tree
