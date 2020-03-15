"""
Defines a tree containing all PyTest test packages, modules, classes and
functions in their respective hierarchy. Used to render the test structure
in the UI and to update with test results as they are available.
"""

from __future__ import annotations
import enum
import textwrap
from typing import Optional, List, Union


class TestStates(enum.Enum):
    """Possible states of a tree node."""

    INIT = enum.auto()
    PASSED = enum.auto()
    FAILED = enum.auto()
    XFAILED = enum.auto()
    SKIPPED = enum.auto()


class TestGroups(enum.Enum):

    ROOT = enum.auto()
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
        self, item, children: Optional[List[Union[BranchNode, LeafNode]]] = None,
    ):
        self.parent = None
        self.item = item
        self.children = children or []
        for child in self.children:
            child.parent = self
        self.status = TestStates.INIT

    def __eq__(self, other: Union[BranchNode, LeafNode]) -> bool:
        """Compare two BranchNodes for equality."""
        if not isinstance(other, BranchNode):
            return False

        return self.item == other.item and self.children == other.children

    def __repr__(self):
        return f"BranchNode <{self.item} {self.status}>"

    def pretty_format(self):
        """Output a pretty-formatted string of the whole tree, for debug purposes."""
        return "{}\n{}".format(
            self,
            textwrap.indent(
                "\n".join(child.pretty_format() for child in self.children), prefix="  "
            ),
        )


class LeafNode:
    """
    A single leaf node in the test tree. A leaf node has no children and
    as such, represents a test function or method.
    """

    def __init__(self, item):
        self.item = item
        self.status = TestStates.INIT

    def __eq__(self, other: Union[BranchNode, LeafNode]) -> bool:
        """Compare two LeafNodes for equality."""
        if not isinstance(other, LeafNode):
            return False

        return self.item == other.item

    def __repr__(self):
        return f"LeafNode <{self.item} {self.status}"

    def pretty_format(self):
        """Output a pretty-formatted string of the whole tree, for debug purposes."""
        return str(self)


def build_from_session(session):
    """Build a result tree from the PyTest session object."""
    root = BranchNode(session)

    for item in session.items:
        collectors = item.listchain()[1:-1]
        branch = _ensure_branch(root, collectors)
        branch.children.append(LeafNode(item))

    return root


def _ensure_branch(node, collectors):
    if not collectors:
        return node

    next_col, rest = collectors[0], collectors[1:]
    for child in node.children:
        if child.item == next_col:
            return _ensure_branch(child, rest)

    new_child = BranchNode(item=next_col)
    node.children.append(new_child)
    return _ensure_branch(new_child, rest)
