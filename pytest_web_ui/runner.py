"""PyTestRunner class and related functions."""
import os
from typing import Union, Tuple, Dict

import pytest  # type: ignore
from _pytest import config  # type: ignore
from _pytest import reports  # type: ignore

from . import result_tree


class PyTestRunner:
    """Owns the test result tree and handles running tests and updating the results."""

    def __init__(self, directory: str):
        self._directory = directory
        self._parent_dir = os.path.dirname(directory)
        self.result_tree, self._result_index = _init_result_tree(directory)
        # self._api = api.Server()

    def run_tests(self, nodeid: str) -> Union[int, config.ExitCode]:
        """
        Run the test or tests for a given PyTest node. Updates the results tree with
        test reports as they are available.
        """
        return pytest.main(
            [os.path.join(self._parent_dir, nodeid)],
            plugins=[TestRunPlugin(self._add_test_report)],
        )

    def _add_test_report(self, report: reports.TestReport):
        """Add a test report into our result tree."""
        self._result_index[report.nodeid].report = report


def _init_result_tree(
    directory: str,
) -> Tuple[result_tree.BranchNode, Dict[str, result_tree.LeafNode]]:
    """Collect the tests and initialise the result tree skeleton."""
    plugin = CollectPlugin()
    ret = pytest.main(["--collect-only", directory], plugins=[plugin])
    if ret != 0:
        raise RuntimeError(f"Failed to collect tests from {directory}")

    session = plugin.session
    return result_tree.build_from_session(session)


class CollectPlugin:
    """PyTest plugin used to retrieve session object after collection."""

    def __init__(self):
        self.session = None

    def pytest_collection_finish(self, session):
        self.session = session


class TestRunPlugin:
    """PyTest plugin used to run tests and store results in our tree."""

    def __init__(self, report_callback):
        self._report_callback = report_callback

    def pytest_runtest_logreport(self, report):
        """
        Hook called after a new test report is ready. Also called for setup/teardown.
        """
        # Currently do nothing for setup/teardown.
        if report.when != "call":
            return
        self._report_callback(report)
