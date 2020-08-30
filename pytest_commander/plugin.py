"""
Provides the interface to running pytest and extracting information via a plugin.
"""

import collections
import logging
import multiprocessing
import os
import queue
from typing import cast, Optional, Union

import pytest  # type: ignore
from _pytest import reports  # type: ignore

from pytest_commander import nodeid
from pytest_commander import result_tree

LOGGER = logging.getLogger(__name__)
DONE = 0xDEAD

TestReport = collections.namedtuple("TestReport", ["outcome", "longrepr", "nodeid"])
CollectReport = collections.namedtuple(
    "CollectReport", ["outcome", "longrepr", "collected_items", "failure_nodeid"]
)


def collect_path(path: str, root_dir: str) -> result_tree.BranchNode:
    if not path.startswith(root_dir):
        raise ValueError(
            f"path {path} does not appear to be within root dir {root_dir}"
        )

    reports_queue: "queue.Queue[Union[result_tree.Node, TestReport, int]]" = queue.Queue()
    plugin = _ReporterPlugin(queue=reports_queue, root_dir=root_dir)
    ret = pytest.main(
        ["--collect-only", f"--rootdir={root_dir}", path], plugins=[plugin]
    )
    if ret != 0:
        LOGGER.warning("Failed to collect tests from %s", path)
    res = reports_queue.get()
    if not isinstance(res, result_tree.BranchNode):
        raise TypeError(f"unexpected return from queue: {res}")
    return cast(result_tree.BranchNode, res)


def run_test(
    test_nodeid: nodeid.Nodeid,
    mp_queue: "multiprocessing.Queue[Union[result_tree.Node, TestReport, int]]",
    root_dir: str,
):
    plugin = _ReporterPlugin(queue=mp_queue, root_dir=root_dir)
    full_path = os.path.join(root_dir, test_nodeid.fspath)
    pytest.main([full_path, f"--rootdir={root_dir}"], plugins=[plugin])
    mp_queue.put(DONE)


class _ReporterPlugin:
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


def _tree_from_collect_report(report: CollectReport, root_dir: str) -> result_tree.Node:
    if report.outcome != "passed":
        failure_nodeid = nodeid.Nodeid.from_string(report.failure_nodeid)
        leaf_node = result_tree.LeafNode(failure_nodeid, root_dir)
        leaf_node.status = result_tree.TestState(report.outcome)
        leaf_node.longrepr = report.longrepr
        return result_tree.build_from_leaf(leaf_node, root_dir)

    return result_tree.build_from_items(report.collected_items, root_dir)

