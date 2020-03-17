"""HTTP API for PyTest runner."""
import logging
import os
from typing import Dict, Any, Tuple

import flask
import flask_socketio  # type: ignore

from pytest_ui_server import runner
from pytest_ui_server import result_tree

LOGGER = logging.getLogger(__name__)


def build_app(directory: str) -> Tuple[flask.Flask, flask_socketio.SocketIO]:
    """Build a Flask app to serve the API and static files."""
    build_dir = os.path.join(os.path.dirname(__file__), os.pardir, "pytest_web_ui", "build")
    index_file = os.path.join(build_dir, "index.html")

    app = flask.Flask(__name__, root_path=build_dir)
    test_runner = runner.PyTestRunner(directory)
    branch_schema = result_tree.BranchNodeSchema()
    leaf_schema = result_tree.LeafNodeSchema()
    socketio = flask_socketio.SocketIO(app)

    @app.route("/")
    def index():
        return flask.send_file(index_file)
    
    @app.route('/js/<path:path>')
    def send_build(path):
        return flask.send_from_directory(path)

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
