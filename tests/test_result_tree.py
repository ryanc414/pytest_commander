"""Unit tests for the result_tree module"""

import collections
import json
import os

import pytest

from pytest_commander import result_tree

SessionItem = collections.namedtuple("SessionItem", ["nodeid"])

ITEMS = [
    SessionItem(nodeid)
    for nodeid in [
        "path/to/test_a.py::TestSuite::test_one",
        "path/to/test_a.py::TestSuite::test_two",
        "path/to/test_a.py::test_one",
        "path/to/test_a.py::test_two",
        "path/to/test_a.py::test_three[1]",
        "path/to/test_a.py::test_three[2]",
        "path/to/test_a.py::test_three[3]",
    ]
]


def test_build_tree(snapshot):
    tree = result_tree.build_from_items(ITEMS, "/root")
    assert isinstance(tree, result_tree.BranchNode)
    assert tree.status == result_tree.TestState.INIT
    assert tree.short_id == "root"
    assert str(tree.nodeid) == ""
    serializer = result_tree.BranchNodeSchema()
    serialized_tree = serializer.dump(tree)
    snapshot.assert_match(serialized_tree)
