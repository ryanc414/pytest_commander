"""PyTestRunner class and related functions."""
from concurrent import futures
import contextlib
import enum
import logging
import os
import multiprocessing
import queue
import subprocess
from typing import Tuple, Dict, Callable, List, Union, Optional, cast
import pprint
import collections

import eventlet  # type: ignore
import flask_socketio  # type: ignore

import pytest  # type: ignore
from _pytest import reports  # type: ignore
from _pytest import nodes  # type: ignore

from pytest_web_ui import result_tree
from pytest_web_ui import environment
from pytest_web_ui import nodeid

LOGGER = logging.getLogger(__name__)
_DONE = 0xDEAD
_ACTIVE_LOOP_SLEEP = 0.1  # seconds


CollectReport = collections.namedtuple(
    "CollectReport", ["outcome", "longrepr", "collected_items", "failure_nodeid"]
)

TestReport = collections.namedtuple("TestReport", ["outcome", "longrepr", "nodeid"])


class PyTestRunner:
    """Owns the test result tree and handles running tests and updating the results."""

    def __init__(
        self, directory: str, socketio: flask_socketio.SocketIO,
    ):
        self._directory = directory
        self.result_tree, self._result_index = _init_result_tree(directory)
        self._socketio = socketio
        self._branch_schema = result_tree.BranchNodeSchema()
        self._leaf_schema = result_tree.LeafNodeSchema()

    @contextlib.contextmanager
    def environment_manager(self):
        """
        Context manager to ensure all test environments are closed on shutdown.
        """
        yield
        _stop_all_environments(self.result_tree)

    def run_tests(self, nodeid: str):
        """
        Run the test or tests for a given PyTest node. Updates the results tree with
        test reports as they are available.
        """
        self._socketio.start_background_task(self._run_test, nodeid)

    def start_env(self, nodeid: str):
        """
        Start the environment for a node. The node must be a branch node that has
        an environment which is not currently started.
        """
        node = self._result_index[nodeid]
        if not isinstance(node, result_tree.BranchNode) or node.environment is None:
            raise ValueError(f"cannot start environment for node {nodeid}")
        node.environment.start()
        self._send_update()

    def stop_env(self, nodeid: str):
        """
        Stop the environment for a node. The node must be a branch node that has
        an environment which is currently started.
        """
        node = self._result_index[nodeid]
        if not isinstance(node, result_tree.BranchNode) or node.environment is None:
            raise ValueError(f"cannot start environment for node {nodeid}")
        node.environment.state = environment.EnvironmentState.STOPPING
        self._send_update()
        self._socketio.start_background_task(self._stop_env, node)

    def _stop_env(self, node: result_tree.BranchNode):
        assert node.environment is not None
        node.environment.stop()
        self._send_update()

    def _run_test(self, nodeid: str):
        result_queue: "multiprocessing.Queue[Union[Tuple[result_tree.Node, Dict[str, result_tree.Node]], TestReport, int]]" = multiprocessing.Queue()
        proc = multiprocessing.Process(
            target=_run_test,
            args=(nodeid, result_queue, self.result_tree.fspath, self._directory),
        )
        LOGGER.debug("running test %s", nodeid)
        proc.start()

        run_tree, index = _get_queue_noblock(result_queue)
        LOGGER.debug("got run_tree %s", run_tree)
        self._result_index.update(index)
        run_tree.status = result_tree.TestState.RUNNING
        parent_node = self._get_parent_node(run_tree.nodeid)

        if parent_node is None:
            self.result_tree = run_tree
        elif isinstance(run_tree, result_tree.BranchNode):
            parent_node.child_branches[run_tree.short_id] = run_tree
        else:
            assert isinstance(run_tree, result_tree.LeafNode)
            parent_node.child_leaves[run_tree.short_id] = run_tree
        self._send_update()

        eventlet.sleep()

        while True:
            val = _get_queue_noblock(result_queue)
            if val == _DONE:
                LOGGER.debug("DONE received, breaking")
                break
            LOGGER.debug("adding test report %s", val)
            self._add_test_report(val)
            self._send_update()

        LOGGER.debug("joining child proc...")
        proc.join()
        LOGGER.debug("child proc joined")

    def _add_test_report(self, report: reports.TestReport):
        """Add a report into our result tree."""
        result_node = self._result_index[report.nodeid]
        assert isinstance(result_node, result_tree.LeafNode)
        result_node.status = result_tree.TestState(report.outcome)
        result_node.longrepr = report.longrepr

    def _get_parent_node(
        self, raw_child_nodeid: str
    ) -> Optional[result_tree.BranchNode]:
        child_nodeid = nodeid.Nodeid.from_string(raw_child_nodeid)
        parent_nodeid = str(child_nodeid.parent)
        if not parent_nodeid:
            return None
        parent_node = self._result_index[parent_nodeid]
        assert isinstance(parent_node, result_tree.BranchNode)
        return cast(result_tree.BranchNode, parent_node)

    def _send_update(self):
        LOGGER.debug("sending update")
        serialized_tree = self._branch_schema.dump(self.result_tree)
        self._socketio.emit("update", serialized_tree)


def _run_test(
    raw_test_nodeid: str,
    mp_queue: "multiprocessing.Queue[Union[Tuple[result_tree.Node, Dict[str, result_tree.Node]], TestReport, int]]",
    root_dir: str,
    test_dir: str,
):

    test_nodeid = nodeid.Nodeid.from_string(raw_test_nodeid)
    parent_nodeid = test_nodeid.parent
    plugin = ReporterPlugin(queue=mp_queue, collect_prefix=str(parent_nodeid))
    pytest.main([test_nodeid.fspath], plugins=[plugin])
    mp_queue.put(_DONE)


def _get_full_path(nodeid: str, root_dir: str, test_dir: str) -> str:
    if not nodeid:
        return test_dir
    return nodeid.replace("/", os.sep)


def _init_result_tree(
    directory: str,
) -> Tuple[result_tree.BranchNode, Dict[str, result_tree.Node]]:
    """Collect the tests and initialise the result tree skeleton."""
    node, index = _init_result_tree_recur(directory)
    if len(node.child_branches) == 0 and len(node.child_leaves) == 0:
        raise RuntimeError(f"failed to collect any tests from {directory}")
    for child_branch in node.child_branches.values():
        result_tree.set_parent_ids(child_branch)
    return node, index


def _init_result_tree_recur(
    directory: str,
) -> Tuple[result_tree.BranchNode, Dict[str, result_tree.Node]]:
    root_node = result_tree.BranchNode(
        nodeid=directory.replace(os.sep, "/"),
        short_id=os.path.basename(directory),
        env=environment.EnvironmentManager(directory),
    )
    nodes_index: Dict[str, result_tree.Node] = {root_node.nodeid: root_node}

    with os.scandir(directory) as it:
        for entry in it:
            if entry.is_file() and entry.name.endswith(".py"):
                node, index = _collect_file(entry.path, directory)
            elif entry.is_dir():
                node, index = _init_result_tree_recur(entry.path)
            else:
                continue

            if isinstance(node, result_tree.LeafNode):
                root_node.child_leaves[node.short_id] = node
                nodes_index.update(index)
            elif list(node.iter_children()):
                root_node.child_branches[node.short_id] = node
                nodes_index.update(index)

    return root_node, nodes_index


def _collect_file(
    filepath: str, collect_prefix: str,
) -> Tuple[result_tree.BranchNode, Dict[str, result_tree.Node]]:
    reports_queue: "queue.Queue[Union[Tuple[result_tree.Node, Dict[str, result_tree.Node]], TestReport, int]]" = queue.Queue()
    plugin = ReporterPlugin(queue=reports_queue, collect_prefix=collect_prefix)
    ret = pytest.main(["--collect-only", filepath], plugins=[plugin])
    if ret != 0:
        LOGGER.warning("Failed to collect tests from %s", filepath)
    res = reports_queue.get()
    if not isinstance(res, tuple):
        raise TypeError(f"unexpected return from queue: {res}")
    return cast(Tuple[result_tree.BranchNode, Dict[str, result_tree.Node]], res)


def _tree_from_collect_report(
    report: CollectReport, collect_prefix: str,
) -> Tuple[result_tree.Node, Dict[str, result_tree.Node]]:
    if report.outcome != "passed":
        node = result_tree.LeafNode(report.failure_nodeid)
        node.status = result_tree.TestState(report.outcome)
        node.longrepr = report.longrepr
        return node, {node.nodeid: node}

    return result_tree.build_from_items(report.collected_items, collect_prefix)


def _stop_all_environments(node: result_tree.BranchNode):
    """Stop all environments recursively from root node downwards."""
    if node.environment is None:
        return

    if node.environment.state == environment.EnvironmentState.STARTED:
        node.environment.state = environment.EnvironmentState.STOPPING
        node.environment.stop()

    for child_node in node.child_branches.values():
        _stop_all_environments(child_node)


def _get_queue_noblock(q: multiprocessing.Queue):
    """
    Receive from a multiprocessing.Queue object without blocking from an
    eventlet green thread. Polls the queue and calls eventlet.sleep() to yield
    to other threads in between.
    """
    while True:
        try:
            return q.get_nowait()
        except queue.Empty:
            eventlet.sleep(_ACTIVE_LOOP_SLEEP)


class ReporterPlugin:
    """PyTest plugin used to run tests and store results in our tree."""

    def __init__(
        self,
        queue: Union[
            "queue.Queue[Union[Tuple[result_tree.Node, Dict[str, result_tree.Node]], TestReport, int]]",
            "multiprocessing.Queue[Union[Tuple[result_tree.Node, Dict[str, result_tree.Node]], TestReport, int]]",
        ],
        collect_prefix: str,
    ):
        self._queue = queue
        self._collect_prefix = collect_prefix
        self._last_collectreport: Optional[reports.CollectReport] = None

    def pytest_collectreport(self, report: reports.CollectReport):
        """Hook called after a test has been collected."""
        self._last_collectreport = report

    def pytest_collection_finish(self, session: pytest.Session):
        if self._last_collectreport is None:
            raise RuntimeError("no collect reports found")
        collect_report = cast(reports.CollectReport, self._last_collectreport)
        report = CollectReport(
            outcome=collect_report.outcome,
            longrepr=collect_report.longrepr,
            failure_nodeid=collect_report.nodeid,
            collected_items=session.items,
        )
        self._queue.put(_tree_from_collect_report(report, self._collect_prefix))

    def pytest_runtest_logreport(self, report: reports.TestReport):
        """
        Hook called after a new test report is ready. Also called for
        setup/teardown.
        """
        # Ignore reports for successful setup/teardown.
        if report.outcome == "passed" and report.when != "call":
            return
        self._queue.put(
            TestReport(
                outcome=report.outcome, longrepr=report.longrepr, nodeid=report.nodeid,
            )
        )
