"""
Defines a tree containing all PyTest test packages, modules, classes and
functions in their respective hierarchy. Used to render the test structure
in the UI and to update with test results as they are available.
"""

from __future__ import annotations
import abc
import enum
import logging
import os
import textwrap
from typing import List, Tuple, Dict, Generator, Iterator, Optional, Any, cast

import marshmallow
from marshmallow import fields
import marshmallow_enum  # type: ignore
from _pytest import nodes  # type: ignore

from pytest_commander import environment
from pytest_commander import nodeid

LOGGER = logging.getLogger(__name__)


class TestState(enum.Enum):
    """Possible states of a tree node."""

    INIT = "init"
    SKIPPED = "skipped"
    PASSED = "passed"
    FAILED = "failed"
    RUNNING = "running"


# A parent entry will inherit the highest precedence state from its children.
_TEST_STATE_PRECEDENT = {
    TestState.INIT: 1,
    TestState.SKIPPED: 2,
    TestState.PASSED: 3,
    TestState.FAILED: 4,
    TestState.RUNNING: 5,
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
    def status(self) -> TestState:
        """Property getter for current status."""
        raise NotImplementedError

    @status.setter
    def status(self, new_status: TestState):
        """Property setter for current status."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def nodeid(self) -> nodeid.Nodeid:
        """Return the unique ID for this node."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def short_id(self) -> str:
        """Return the short ID label for this node."""
        raise NotImplementedError

    @abc.abstractmethod
    def pretty_format(self) -> str:
        """
        Format this node and its children recursively as a multi-line string, for debug
        purposes.
        """
        raise NotImplementedError


class BranchNode(Node):
    """
    A single branch node in the test tree. A branch node has at least one
    child - as such, this object represents a collection of testcases. The
    collection may be a test package, module or a class.
    """

    def __init__(
        self,
        branch_nodeid: nodeid.Nodeid,
        root_dir: str,
        short_id: Optional[str] = None,
    ):
        self._nodeid = branch_nodeid
        self._short_id = short_id
        self._fspath = os.path.join(root_dir, branch_nodeid.fspath)
        self.child_branches: Dict[str, BranchNode] = {}
        self.child_leaves: Dict[str, LeafNode] = {}

        self.environment: Optional[environment.EnvironmentManager]
        if os.path.isdir(self._fspath):
            self.environment = environment.EnvironmentManager(self._fspath)
        else:
            self.environment = None

    def __eq__(self, other: object) -> bool:
        """Compare two BranchNodes for equality."""
        if not isinstance(other, BranchNode):
            return False

        return self.nodeid == other.nodeid

    def __repr__(self) -> str:
        """String representation of this node."""
        return f"BranchNode <{self.nodeid} {self.status}>"

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
    def environment_state(self):
        if self.environment is None:
            return environment.EnvironmentState.INACTIVE

        return self.environment.state

    @property
    def nodeid(self) -> nodeid.Nodeid:
        """Unique ID of this node, used for indexing."""
        return self._nodeid

    @property
    def short_id(self) -> str:
        """Short ID."""
        if self._short_id:
            return self._short_id
        return self.nodeid.short_id

    @property
    def fspath(self) -> str:
        """Filesystem path this test node corresponds to."""
        return self._fspath

    @property
    def status(self) -> TestState:
        """Return status of child entries."""
        return _status_precedent(child.status for child in self.iter_children())

    @status.setter
    def status(self, new_status: TestState):
        for child in self.iter_children():
            child.status = new_status


class LeafNode(Node):
    """
    A single leaf node in the test tree. A leaf node has no children and
    as such, represents a test function or method.
    """

    def __init__(self, leaf_nodeid: nodeid.Nodeid, root_dir: str):
        self._nodeid = leaf_nodeid
        self._status = TestState.INIT
        self._fspath = os.path.join(root_dir, leaf_nodeid.fspath)
        self.longrepr = None

    def __eq__(self, other: object) -> bool:
        """Compare two LeafNodes for equality."""
        if not isinstance(other, LeafNode):
            return False

        return self.nodeid == other.nodeid

    def __repr__(self) -> str:
        """String representation of this node."""
        return f"LeafNode <{self.nodeid} {self.status}>"

    @property
    def nodeid(self) -> nodeid.Nodeid:
        return self._nodeid

    @property
    def short_id(self) -> str:
        """Short ID."""
        return self.nodeid.short_id

    @property
    def fspath(self) -> str:
        """Filesystem path this test node corresponds to."""
        return self._fspath

    def pretty_format(self) -> str:
        """Output a pretty-formatted string of the whole tree, for debug purposes."""
        return str(self)

    @property
    def status(self) -> TestState:
        """
        Get the status of this entry. If there is a test report that means the test has
        run and we get the status from the report. Otherwise, the status may be either
        INIT (not yet run) or RUNNING (in progress of being run).
        """
        return self._status

    @status.setter
    def status(self, new_status):
        """
        Update the status. This is only called to either set this node as RUNNING or
        reset the state to INIT. In either case, we reset the test report to None if
        present.
        """
        self._status = new_status


def build_from_items(items: List, root_dir: str) -> Node:
    """Build a result tree from the PyTest session object."""
    child_branches: Dict[str, BranchNode] = {}
    child_leaves: Dict[str, LeafNode] = {}

    for item in items:
        item_nodeid = nodeid.Nodeid.from_string(item.nodeid)
        nodeid_fragments = item_nodeid.fragments
        leaf = LeafNode(nodeid.Nodeid.from_string(item.nodeid), root_dir)

        if len(nodeid_fragments) > 1:
            child = _ensure_branch(
                child_branches, nodeid_fragments, nodeid.EMPTY_NODEID, root_dir
            )
            child.child_leaves[leaf.short_id] = leaf
        else:
            assert len(nodeid_fragments) == 1
            child_leaves[leaf.short_id] = leaf

    short_id = os.path.basename(root_dir.rstrip(os.sep))
    root = BranchNode(
        branch_nodeid=nodeid.EMPTY_NODEID, root_dir=root_dir, short_id=short_id
    )
    root.child_branches = child_branches
    root.child_leaves = child_leaves

    return root


def _ensure_branch(
    child_branches: Dict[str, BranchNode],
    nodeid_fragments: List[nodeid.NodeidFragment],
    nodeid_prefix: nodeid.Nodeid,
    root_dir: str,
) -> BranchNode:
    """
    Retrieve the branch node under the given root node that corresponds to the given
    chain of collectors. If any branch nodes do not yet exist, they will be
    automatically created.
    """
    next_fragment, rest_fragments = nodeid_fragments[0], nodeid_fragments[1:]
    child_nodeid = nodeid_prefix.append(next_fragment)

    try:
        child = child_branches[next_fragment.val]
        assert child.nodeid == child_nodeid
    except KeyError:
        child = BranchNode(branch_nodeid=child_nodeid, root_dir=root_dir)
        child_branches[next_fragment.val] = child

    if len(rest_fragments) > 1:
        return _ensure_branch(
            child.child_branches, rest_fragments, child_nodeid, root_dir
        )
    elif len(rest_fragments) == 1:
        return child
    else:
        raise RuntimeError


class NodeSchema(marshmallow.Schema):
    """Base schema for all nodes."""

    nodeid = fields.Str()
    short_id = fields.Str()
    status = marshmallow_enum.EnumField(TestState, by_value=True)


class LeafNodeSchema(NodeSchema):
    """Serialization schema for leaf nodes."""

    longrepr = fields.Str(allow_none=True)


class BranchNodeSchema(NodeSchema):
    """Serialization schema for branch nodes."""

    child_branches = fields.Dict(
        fields.Str(), fields.Nested(lambda: BranchNodeSchema())
    )
    child_leaves = fields.Dict(fields.Str(), fields.Nested(LeafNodeSchema()))
    environment_state = marshmallow_enum.EnumField(
        environment.EnvironmentState, by_value=True
    )


class Indexer:
    """Indexer allows read-only access to a result tree from a given nodeid."""

    def __init__(self, root: BranchNode):
        self._root = root

    def __getitem__(self, item_nodeid: nodeid.Nodeid) -> Node:
        node = self._root
        for frag in item_nodeid:
            try:
                node = node.child_branches[frag.val]
            except KeyError:
                return node.child_leaves[frag.val]

        return node
