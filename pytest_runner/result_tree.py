"""
Defines a tree containing all PyTest test packages, modules, classes and
functions in their respective hierarchy. Used to render the test structure
in the UI and to update with test results as they are available.
"""

from __future__ import annotations
import enum
import textwrap
from typing import Optional, List, Union, Tuple, Dict

from _pytest import nodes  # type: ignore


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
        self,
        collector: nodes.Collector,
        children: Optional[List[Union[BranchNode, LeafNode]]] = None,
    ):
        self.pytest_node = collector
        self.children = children or []
        self.status = TestStates.INIT

    def __eq__(self, other: object) -> bool:
        """Compare two BranchNodes for equality."""
        if not isinstance(other, BranchNode):
            return False

        return self.pytest_node == other.pytest_node and self.children == other.children

    def __repr__(self) -> str:
        return f"BranchNode <{self.pytest_node} {self.status}>"

    def pretty_format(self) -> str:
        """Output a pretty-formatted string of the whole tree, for debug purposes."""
        formatted_children = textwrap.indent(
            "\n".join(child.pretty_format() for child in self.children), prefix="  "
        )
        return f"{self}\n{formatted_children}"


class LeafNode:
    """
    A single leaf node in the test tree. A leaf node has no children and
    as such, represents a test function or method.
    """

    def __init__(self, item: nodes.Item):
        self.pytest_node = item
        self.status = TestStates.INIT
        self.report = None

    def __eq__(self, other: object) -> bool:
        """Compare two LeafNodes for equality."""
        if not isinstance(other, LeafNode):
            return False

        return self.pytest_node == other.pytest_node

    def __repr__(self) -> str:
        return f"LeafNode <{self.pytest_node} {self.status}>"

    def pretty_format(self) -> str:
        """Output a pretty-formatted string of the whole tree, for debug purposes."""
        return str(self)


def build_from_session(
    session: nodes.Session,
) -> Tuple[BranchNode, Dict[str, LeafNode]]:
    """Build a result tree from the PyTest session object."""
    root = BranchNode(session)
    index = {}

    for item in session.items:
        collectors = item.listchain()[1:-1]
        branch = _ensure_branch(root, collectors)
        leaf = LeafNode(item)
        branch.children.append(leaf)
        index[item.nodeid] = leaf

    return root, index


def _ensure_branch(node: BranchNode, collectors: List[nodes.Collector]) -> BranchNode:
    if not collectors:
        return node

    next_col, rest = collectors[0], collectors[1:]
    for child in node.children:
        if child.pytest_node == next_col:
            assert isinstance(child, BranchNode)
            return _ensure_branch(child, rest)

    new_child = BranchNode(collector=next_col)
    node.children.append(new_child)
    return _ensure_branch(new_child, rest)
