"""
Defines a tree containing all PyTest test packages, modules, classes and
functions in their respective hierarchy. Used to render the test structure
in the UI and to update with test results as they are available.
"""

from __future__ import annotations
import enum
import os
from typing import Optional, List, Union


class TestStates(enum.Enum):
    """Possible states of a tree node."""

    INIT = enum.auto()
    PASSED = enum.auto()
    FAILED = enum.auto()
    XFAILED = enum.auto()
    SKIPPED = enum.auto()


class TestGroups(enum.Enum):

    PACKAGE = enum.auto()
    MODULE = enum.auto()
    CLASS = enum.auto()


class BranchNode:
    """
    A single branch node in the test tree. A branch node has at least one
    child - as such, this object represents a collection of testcases. The
    collection may be a test package, module or a class.
    """

    def __init__(
        self,
        group_type: TestGroups,
        name: str,
        parent: Optional[BranchNode] = None,
        children: Optional[List[Union[BranchNode, LeafNode]]] = None,
    ):
        self.group_type = group_type
        self.name = name
        self.parent = parent
        self.children = children or []
        for child in self.children:
            child.parent = self
        self.status = TestStates.INIT


class LeafNode:
    """
    A single leaf node in the test tree. A leaf node has no children and
    as such, represents a test function or method.
    """

    def __init__(self, name: str, parent: BranchNode = None):
        self.name = name
        self.parent = parent
        self.status = TestStates.INIT


def full_path(tree_node: Union[BranchNode, LeafNode]) -> str:
    """
    Return the full path of a node in the tree from the root.

    E.g. test_module.py::TestSuite::test_method
    """
    if tree_node.parent is None:
        return tree_node.name

    separator = _get_separator(tree_node.parent.group_type)
    parent_path = full_path(tree_node.parent)

    return separator.join((parent_path, tree_node.name))


def _get_separator(parent_type: TestGroups) -> str:
    if parent_type == TestGroups.PACKAGE:
        return os.path.sep
    return "::"
