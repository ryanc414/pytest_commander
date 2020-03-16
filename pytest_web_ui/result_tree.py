"""
Defines a tree containing all PyTest test packages, modules, classes and
functions in their respective hierarchy. Used to render the test structure
in the UI and to update with test results as they are available.
"""

from __future__ import annotations
import abc
import enum
import textwrap
from typing import List, Tuple, Dict, Generator, Iterator, Optional

import marshmallow
from marshmallow import fields
from _pytest import nodes  # type: ignore


class TestState(enum.Enum):
    """Possible states of a tree node."""

    INIT = "init"
    SKIPPED = "skipped"
    PASSED = "passed"
    FAILED = "failed"


_TEST_STATE_PRECEDENT = {
    TestState.INIT: 1,
    TestState.SKIPPED: 2,
    TestState.PASSED: 3,
    TestState.FAILED: 4,
}


def _status_precedent(statuses: Iterator[TestState]) -> TestState:
    """
    Return the status with the highest precedence. If the iterator is empty, INIT state
    is returned as a default.
    """
    return max(
        statuses,
        key=lambda status: _TEST_STATE_PRECEDENT[status],
        default=TestState.INIT,
    )


class Node(abc.ABC):
    """Define common interface for branch and leaf nodes."""

    @property
    @abc.abstractmethod
    def nodeid(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def status(self) -> TestState:
        raise NotImplementedError

    @abc.abstractmethod
    def pretty_format(self) -> str:
        raise NotImplementedError


class BranchNode(Node):
    """
    A single branch node in the test tree. A branch node has at least one
    child - as such, this object represents a collection of testcases. The
    collection may be a test package, module or a class.
    """

    def __init__(
        self, collector: nodes.Collector,
    ):
        self._pytest_node = collector
        self.child_branches: Dict[str, BranchNode] = {}
        self.child_leaves: Dict[str, LeafNode] = {}

    def __eq__(self, other: object) -> bool:
        """Compare two BranchNodes for equality."""
        if not isinstance(other, BranchNode):
            return False

        return self._pytest_node == other._pytest_node

    def __repr__(self) -> str:
        return f"BranchNode <{self._pytest_node} {self.status}>"

    def pretty_format(self) -> str:
        """Output a pretty-formatted string of the whole tree, for debug purposes."""
        formatted_children = textwrap.indent(
            "\n".join(child.pretty_format() for child in self.iter_children()),
            prefix="  ",
        )
        return f"{self}\n{formatted_children}"

    def iter_children(self) -> Generator[Node, None, None]:
        """Iterate over all child branches and leaves."""
        for branch in self.child_branches.values():
            yield branch
        for leaf in self.child_leaves.values():
            yield leaf

    @property
    def nodeid(self) -> str:
        """Unique ID of this node, used for indexing."""
        return self._pytest_node.nodeid

    @property
    def status(self) -> TestState:
        """Return status of child entries."""
        return _status_precedent(child.status for child in self.iter_children())


class LeafNode(Node):
    """
    A single leaf node in the test tree. A leaf node has no children and
    as such, represents a test function or method.
    """

    def __init__(self, item: nodes.Item):
        self._pytest_node = item
        self.report = None

    def __eq__(self, other: object) -> bool:
        """Compare two LeafNodes for equality."""
        if not isinstance(other, LeafNode):
            return False

        return self._pytest_node == other._pytest_node

    def __repr__(self) -> str:
        return f"LeafNode <{self._pytest_node} {self.status}>"

    @property
    def nodeid(self) -> str:
        return self._pytest_node.nodeid

    @property
    def status(self) -> TestState:
        if self.report is None:
            return TestState.INIT
        return self.report.outcome

    @property
    def longrepr(self) -> Optional[str]:
        if self.report is None:
            return None
        return str(self.report.longrepr)

    def pretty_format(self) -> str:
        """Output a pretty-formatted string of the whole tree, for debug purposes."""
        return str(self)


def build_from_session(
    session: nodes.Session,
) -> Tuple[BranchNode, Dict[str, LeafNode]]:
    """Build a result tree from the PyTest session object."""
    root = BranchNode(session)
    leaves_index = {}

    for item in session.items:
        collectors = item.listchain()[1:-1]
        branch = _ensure_branch(root, collectors)
        leaf = LeafNode(item)
        branch.child_leaves[leaf.nodeid] = leaf
        leaves_index[item.nodeid] = leaf

    return root, leaves_index


def _ensure_branch(node: BranchNode, collectors: List[nodes.Collector]) -> BranchNode:
    """
    Retrieve the branch node under the given root node that corresponds to the given
    chain of collectors. If any branch nodes do not yet exist, they will be
    automatically created.
    """
    # Base recursive case: return the current node if the list of collectors is empty.
    if not collectors:
        return node

    next_col, rest = collectors[0], collectors[1:]

    try:
        child = node.child_branches[next_col.nodeid]
    except KeyError:
        child = BranchNode(collector=next_col)
        node.child_branches[next_col.nodeid] = child

    return _ensure_branch(child, rest)


class LeafNodeSchema(marshmallow.Schema):
    """Serialization schema for leaf nodes."""

    nodeid = fields.Str()
    status = fields.Str()
    longrepr = fields.Str(allow_none=True)


class BranchNodeSchema(marshmallow.Schema):
    """Serialization schema for branch nodes."""

    nodeid = fields.Str()
    status = fields.Str()
    child_branches = fields.Dict(
        fields.Str(), fields.Nested(lambda: BranchNodeSchema())
    )
    child_leaves = fields.Dict(fields.Str(), fields.Nested(LeafNodeSchema()))
