"""PyTestRunner class and related functions."""
import logging
import os
from typing import Tuple, Dict, Callable
import flask_socketio  # type: ignore

import pytest  # type: ignore
from _pytest import reports  # type: ignore

from pytest_web_ui import result_tree

LOGGER = logging.getLogger(__name__)


class PyTestRunner:
    """Owns the test result tree and handles running tests and updating the results."""

    def __init__(self, directory: str, socketio: flask_socketio.SocketIO):
        self._directory = directory
        self.result_tree, self._result_index = _init_result_tree(directory)
        self._socketio = socketio
        self._branch_schema = result_tree.BranchNodeSchema()
        self._leaf_schema = result_tree.LeafNodeSchema()

    def run_tests(self, nodeid: str):
        """
        Run the test or tests for a given PyTest node. Updates the results tree with
        test reports as they are available.
        """
        result_node = self._result_index[nodeid]
        result_node.status = result_tree.TestState.RUNNING
        self._send_update(result_node)

        self._socketio.start_background_task(
            self._run_test, nodeid,
        )

    def _run_test(self, nodeid):
        """
        Runs a test or tests at the given nodeid, update our report tree
        and notify the update over the websocket.
        """
        full_path = self._get_full_path(nodeid)
        LOGGER.info("full_path: %s", full_path)
        pytest.main([full_path], plugins=[TestRunPlugin(self._add_test_report)])
        self._send_update(self._result_index[nodeid])

    def _get_full_path(self, nodeid: str) -> str:
        if not nodeid:
            return self._directory
        return str(self.result_tree.fspath / nodeid.replace("/", os.sep))

    def _add_test_report(self, report: reports.TestReport):
        """Add a test report into our result tree."""
        result_node = self._result_index[report.nodeid]
        assert isinstance(result_node, result_tree.LeafNode)
        result_node.report = report

    def _send_update(self, updated_node: result_tree.Node):
        if not updated_node.nodeid:
            parents_slice = self._branch_schema.dump(updated_node)
        else:
            parents_slice, parent_node = result_tree.serialize_parents_slice(
                updated_node, self.result_tree
            )

            if isinstance(updated_node, result_tree.BranchNode):
                serialized_result = self._branch_schema.dump(updated_node)
                parent_node["child_branches"] = {
                    updated_node.short_id: serialized_result
                }
            elif isinstance(updated_node, result_tree.LeafNode):
                serialized_result = self._leaf_schema.dump(updated_node)
                parent_node["child_leaves"] = {updated_node.short_id: serialized_result}
            else:
                raise TypeError(f"Unexpected node type: {type(updated_node)}")

        LOGGER.debug("Sending update for nodeid %s", updated_node.nodeid)
        self._socketio.emit("update", parents_slice)


def _init_result_tree(
    directory: str,
) -> Tuple[result_tree.BranchNode, Dict[str, result_tree.Node]]:
    """Collect the tests and initialise the result tree skeleton."""
    plugin = CollectPlugin()
    ret = pytest.main(["--collect-only", directory], plugins=[plugin])
    if ret != 0:
        raise RuntimeError(f"Failed to collect tests from {directory}")

    session = plugin.session
    return result_tree.build_from_session(session, directory)


class CollectPlugin:
    """PyTest plugin used to retrieve session object after collection."""

    def __init__(self):
        self.session = None

    def pytest_collection_finish(self, session):
        self.session = session


class TestRunPlugin:
    """PyTest plugin used to run tests and store results in our tree."""

    def __init__(
        self, report_callback: Callable[[reports.TestReport], None],
    ):
        self._report_callback = report_callback

    def pytest_runtest_logreport(self, report):
        """
        Hook called after a new test report is ready. Also called for
        setup/teardown.
        """
        # Currently do nothing for setup/teardown.
        if report.when != "call":
            return
        self._report_callback(report)
