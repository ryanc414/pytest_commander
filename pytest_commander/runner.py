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
from pytest_commander import plugin
from pytest_commander import watcher

LOGGER = logging.getLogger(__name__)
_ACTIVE_LOOP_SLEEP = 0.1  # seconds


class PyTestRunner:
    """Owns the test result tree and handles running tests and updating the results."""

    def __init__(
        self, directory: str, socketio: flask_socketio.SocketIO, watch_filesystem: bool
    ):
        self._directory = directory
        self.result_tree = _init_result_tree(directory)
        self._socketio = socketio
        self._branch_schema = result_tree.BranchNodeSchema()
        self._leaf_schema = result_tree.LeafNodeSchema()
        self._node_index = result_tree.Indexer(self.result_tree)
        self._watch_filesystem = watch_filesystem
        self._watchdog_proc: Optional[multiprocessing.Process] = None

    def __enter__(self):
        """Context manager entry: start filesystem observer."""
        if self._watch_filesystem:
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
        if self._watchdog_proc is not None:
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
        result_queue: "multiprocessing.Queue[Union[result_tree.Node, plugin.TestReport, int]]" = multiprocessing.Queue()
        proc = multiprocessing.Process(
            target=plugin.run_test, args=(test_nodeid, result_queue, self._directory),
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
            if val == plugin.DONE:
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
            try:
                self._handle_fs_event(event)
            except Exception:
                LOGGER.exception("unexpected error while handling filesystem event")

    def _handle_fs_event(self, event: events.FileSystemEvent):
        if _should_drop_fs_event(event):
            return

        if isinstance(event, (events.FileCreatedEvent, events.FileModifiedEvent)):
            self._handle_file_update(event.src_path)
        elif isinstance(event, events.FileDeletedEvent):
            self._handle_file_deleted(event.src_path)
        elif isinstance(event, events.FileMovedEvent):
            self._handle_file_moved(event.src_path, event.dest_path)
        else:
            LOGGER.debug("dropping filesystem event: %s", event)

    def _handle_file_update(self, filepath: str):
        """Handle a file being created or modified."""
        root_node = plugin.collect_path(filepath, self._directory)
        self.result_tree.merge(root_node)
        self._send_update()

    def _handle_file_deleted(self, filepath: str):
        """Handle a file being deleted."""
        deleted_nodeid = nodeid.Nodeid.from_path(filepath, self._directory)
        try:
            self._pop_node(deleted_nodeid)
        except KeyError:
            LOGGER.debug("could not find node in tree: %s", deleted_nodeid)
            return
        self._send_update()

    def _handle_file_moved(self, src_path: str, dest_path: str):
        """Handle a file being moved."""
        orig_nodeid = nodeid.Nodeid.from_path(src_path, self._directory)
        try:
            self._pop_node(orig_nodeid)
        except KeyError:
            LOGGER.debug("could not find node in tree: %s", orig_nodeid)
            return
        collect_root = plugin.collect_path(dest_path, self._directory)
        self.result_tree.merge(collect_root)
        self._send_update()

    def _pop_node(self, pop_nodeid: nodeid.Nodeid) -> result_tree.Node:
        """Remove and returns a node with a given nodeid from the tree."""
        parent_node = self._node_index[pop_nodeid.parent]
        if not isinstance(parent_node, result_tree.BranchNode):
            raise TypeError(f"parent node is not a branch: {parent_node}")
        short_id = pop_nodeid.short_id

        node: result_tree.Node
        try:
            node = parent_node.child_branches.pop(short_id)
        except KeyError:
            LOGGER.exception("could not pop branch %s", pop_nodeid)
            node = parent_node.child_leaves.pop(short_id)

        self._remove_if_dangling(parent_node)
        return node

    def _remove_if_dangling(self, node: result_tree.BranchNode):
        """Remove a node if it has no children. Recurse up the tree."""
        if not node.child_branches and not node.child_leaves:
            parent_node = self._get_parent_node(node.nodeid)
            if parent_node is None:
                return
            del parent_node.child_branches[node.short_id]
            self._remove_if_dangling(parent_node)


def _should_drop_fs_event(event: events.FileSystemEvent) -> bool:
    if not event.src_path.endswith(".py"):
        LOGGER.debug("dropping event not related to a .py file: %s", event)
        return True

    if any(
        path_el.startswith(".") or path_el == "__pycache__"
        for path_el in event.src_path.split(os.sep)
    ):
        LOGGER.debug("dropping event for hidden file: %s", event)
        return True

    return False


def _init_result_tree(directory: str,) -> result_tree.BranchNode:
    """Collect the tests and initialise the result tree skeleton."""
    root_node = plugin.collect_path(directory, directory)

    if len(root_node.child_branches) == 0 and len(root_node.child_leaves) == 0:
        raise RuntimeError(f"failed to collect any tests from {directory}")

    return root_node


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

