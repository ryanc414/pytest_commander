"""Unit test for the result_tree package."""
import os

from pytest_runner import result_tree


def test_full_path():
    """Test getting the full path of a node in the tree."""
    tree = result_tree.BranchNode(
        group_type=result_tree.TestGroups.PACKAGE,
        name="test_pkg",
        children=[
            result_tree.BranchNode(
                group_type=result_tree.TestGroups.MODULE,
                name="test_mod.py",
                children=[
                    result_tree.BranchNode(
                        group_type=result_tree.TestGroups.CLASS,
                        name="TestSuite",
                        children=[result_tree.LeafNode(name="test_func")],
                    )
                ],
            )
        ],
    )

    expected_path = "test_pkg{}test_mod.py::TestSuite::test_func".format(os.path.sep)
    assert (
        result_tree.full_path(tree.children[0].children[0].children[0]) == expected_path
    )
