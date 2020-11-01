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


def test_parameterized_tests_removed(snapshot):
    items = [
        SessionItem(nodeid)
        for nodeid in [
            "path/to/test_params.py::test_params[alpha]",
            "path/to/test_params.py::test_params[beta]",
            "path/to/test_params.py::test_params[gamma]",
        ]
    ]

    items_missing_one_parameter = items[:2]
    tree = result_tree.build_from_items(items, "/root")
    tree_missing_one_parameter = result_tree.build_from_items(
        items_missing_one_parameter, "/root"
    )
    assert len(items) == 3
    assert len(items_missing_one_parameter) == 2
    serializer = result_tree.BranchNodeSchema()
    serialized_tree = serializer.dump(tree)
    tree.merge(tree_missing_one_parameter)
    serialized_tree_after_merge = serializer.dump(tree)
    snapshot.assert_match(serialized_tree, "before_merge")
    snapshot.assert_match(serialized_tree_after_merge, "after_merge")
