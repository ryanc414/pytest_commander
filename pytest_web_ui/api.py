"""HTTP API for PyTest runner."""
import logging
import queue
from typing import Dict, Any, Tuple

import flask
import flask_socketio

from . import runner
from . import result_tree

LOGGER = logging.getLogger(__name__)


def build_app(directory: str) -> Tuple[flask.Flask, flask_socketio.SocketIO]:
    """Build a Flask app to serve the API and static files."""
    app = flask.Flask(__name__)
    test_runner = runner.PyTestRunner(directory)
    branch_schema = result_tree.BranchNodeSchema()
    leaf_schema = result_tree.LeafNodeSchema()
    socketio = flask_socketio.SocketIO(app)

    @app.route("/api/v1/result-tree")
    def tree() -> Dict[str, Any]:
        return branch_schema.dump(test_runner.result_tree)

    @socketio.on("run test")
    def run_test(nodeid):
        LOGGER.info("Running test: %s", nodeid)

        def update_callback(result: result_tree.Node):
            if isinstance(result, result_tree.BranchNode):
                serialized_result = branch_schema.dump(result)
            elif isinstance(result, result_tree.LeafNode):
                serialized_result = leaf_schema.dump(result)
            else:
                raise TypeError(f"Unexpected result type: {type(result)}")

            flask_socketio.emit("update", serialized_result)

        test_runner.run_tests(nodeid, update_callback)

    return app, socketio
