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
import time
import traceback

import eventlet  # type: ignore
import flask_socketio  # type: ignore
import pytest  # type: ignore
from _pytest import reports  # type: ignore
from _pytest import nodes  # type: ignore
from watchdog import events  # type: ignore
from watchdog import observers  # type: ignore

from pytest_commander import result_tree
from pytest_commander import environment
from pytest_commander import nodeid
from pytest_commander import watcher

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
        self.result_tree = _init_result_tree(directory)
        self._socketio = socketio
        self._branch_schema = result_tree.BranchNodeSchema()
        self._leaf_schema = result_tree.LeafNodeSchema()
        self._node_index = result_tree.Indexer(self.result_tree)
        self._watchdog_proc: Optional[multiprocessing.Process] = None

    def __enter__(self):
        """Context manager entry: start filesystem observer."""
        queue = multiprocessing.Queue()
        self._watchdog_proc = multiprocessing.Process(
            target=watcher.watch_filesystem, args=(self._directory, queue)
        )
        self._watchdog_proc.start()
        self._socketio.start_background_task(self._watch_fs_events, queue)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit: stop filesystem observer and any running
        environments.
        """
        _stop_all_environments(self.result_tree)
        self._watchdog_proc.terminate()
        self._watchdog_proc.join()

    def run_tests(self, raw_test_nodeid: str):
        """
        Run the test or tests for a given PyTest node. Updates the results tree with
        test reports as they are available.
        """
        test_nodeid = nodeid.Nodeid.from_string(raw_test_nodeid)
        self._node_index[test_nodeid].status = result_tree.TestState.RUNNING
        self._send_update()
        self._socketio.start_background_task(self._run_test, test_nodeid)

    def start_env(self, env_nodeid: str):
        """
        Start the environment for a node. The node must be a branch node that has
        an environment which is not currently started.
        """
        node = self._node_index[nodeid.Nodeid.from_string(env_nodeid)]
        if not isinstance(node, result_tree.BranchNode) or node.environment is None:
            raise ValueError(f"cannot start environment for node {nodeid}")
        node.environment.start()
        self._send_update()

    def stop_env(self, env_nodeid: str):
        """
        Stop the environment for a node. The node must be a branch node that has
        an environment which is currently started.
        """
        node = self._node_index[nodeid.Nodeid.from_string(env_nodeid)]
        if not isinstance(node, result_tree.BranchNode) or node.environment is None:
            raise ValueError(f"cannot start environment for node {nodeid}")
        node.environment.state = environment.EnvironmentState.STOPPING
        self._send_update()
        self._socketio.start_background_task(self._stop_env, node)

    def _stop_env(self, node: result_tree.BranchNode):
        assert node.environment is not None
        node.environment.stop()
        self._send_update()

    def _run_test(self, test_nodeid: nodeid.Nodeid):
        result_queue: "multiprocessing.Queue[Union[result_tree.Node, TestReport, int]]" = multiprocessing.Queue()
        proc = multiprocessing.Process(
            target=_run_test, args=(test_nodeid, result_queue, self._directory),
        )
        LOGGER.debug("running test %s", nodeid)
        proc.start()

        run_tree = _get_queue_noblock(result_queue)
        LOGGER.debug("got run_tree %s", run_tree)

        self.result_tree.merge(run_tree)
        node = self._node_index[test_nodeid]
        if node.status == result_tree.TestState.INIT:
            node.status = result_tree.TestState.RUNNING

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
        result_node = self._node_index[nodeid.Nodeid.from_string(report.nodeid)]
        assert isinstance(result_node, result_tree.LeafNode)
        result_node.status = result_tree.TestState(report.outcome)
        result_node.longrepr = report.longrepr

    def _get_parent_node(
        self, child_nodeid: nodeid.Nodeid
    ) -> Optional[result_tree.BranchNode]:
        if not child_nodeid.raw:
            return None

        parent_nodeid = child_nodeid.parent
        parent_node = self._node_index[parent_nodeid]
        assert isinstance(parent_node, result_tree.BranchNode)
        return cast(result_tree.BranchNode, parent_node)

    def _send_update(self):
        LOGGER.debug("sending update")
        serialized_tree = self._branch_schema.dump(self.result_tree)
        self._socketio.emit("update", serialized_tree)

    def _watch_fs_events(self, queue: multiprocessing.Queue):
        while True:
            event = _get_queue_noblock(queue)

            if isinstance(event, events.FileCreatedEvent):
                self._handle_file_created(event.src_path)
            else:
                LOGGER.critical("*** dropping filesystem event: %s", event)

    def _handle_file_created(self, filepath: str):
        """Handle a new file being created."""
        root_node = _collect_path(filepath, self._directory)
        self.result_tree.merge(root_node)
        self._send_update()


def _run_test(
    test_nodeid: nodeid.Nodeid,
    mp_queue: "multiprocessing.Queue[Union[result_tree.Node, TestReport, int]]",
    root_dir: str,
):
    plugin = ReporterPlugin(queue=mp_queue, root_dir=root_dir)
    full_path = os.path.join(root_dir, test_nodeid.fspath)
    pytest.main([full_path, f"--rootdir={root_dir}"], plugins=[plugin])
    mp_queue.put(_DONE)


def _init_result_tree(directory: str,) -> result_tree.BranchNode:
    """Collect the tests and initialise the result tree skeleton."""
    root_node = _collect_path(directory, directory)

    if len(root_node.child_branches) == 0 and len(root_node.child_leaves) == 0:
        raise RuntimeError(f"failed to collect any tests from {directory}")

    return root_node


def _collect_path(path: str, root_dir: str) -> result_tree.BranchNode:
    if not path.startswith(root_dir):
        raise ValueError(
            f"path {path} does not appear to be within root dir {root_dir}"
        )

    reports_queue: "queue.Queue[Union[result_tree.Node, TestReport, int]]" = queue.Queue()
    plugin = ReporterPlugin(queue=reports_queue, root_dir=root_dir)
    ret = pytest.main(
        ["--collect-only", f"--rootdir={root_dir}", path], plugins=[plugin]
    )
    if ret != 0:
        LOGGER.warning("Failed to collect tests from %s", path)
    res = reports_queue.get()
    if not isinstance(res, result_tree.BranchNode):
        raise TypeError(f"unexpected return from queue: {res}")
    return cast(result_tree.BranchNode, res)


def _tree_from_collect_report(report: CollectReport, root_dir: str) -> result_tree.Node:
    if report.outcome != "passed":
        return result_tree.build_from_collect_fail(
            nodeid.Nodeid.from_string(report.failure_nodeid),
            report.outcome,
            report.longrepr,
            root_dir,
        )

    return result_tree.build_from_items(report.collected_items, root_dir)


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
        queue: "queue.Queue[Union[result_tree.Node, TestReport, int]]",
        root_dir: str,
    ):
        self._queue = queue
        self._last_collectreport: Optional[reports.CollectReport] = None
        self._root_dir = root_dir

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
        collected_tree = _tree_from_collect_report(report, self._root_dir)
        if collect_report.outcome != "passed":
            collected_tree.status = result_tree.TestState(collect_report.outcome)
        self._queue.put(collected_tree)

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
