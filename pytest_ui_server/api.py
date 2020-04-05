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
    build_dir = os.path.join(
        os.path.dirname(__file__), os.pardir, "pytest_web_ui", "build"
    )
    static_dir = os.path.join(build_dir, "static")
    index_file = os.path.join(build_dir, "index.html")

    app = flask.Flask(__name__, root_path=build_dir, static_folder=static_dir)
    branch_schema = result_tree.BranchNodeSchema()
    shallow_branch_schema = result_tree.NodeSchema()
    leaf_schema = result_tree.LeafNodeSchema()
    socketio = flask_socketio.SocketIO(app)
    test_runner = runner.PyTestRunner(directory, socketio)

    @app.route("/")
    def index():
        return flask.send_file(index_file)

    @app.route("/<path:path>")
    def send_build(path):
        LOGGER.debug("Sending file: %s", path)
        return flask.send_from_directory(build_dir, path)

    @app.route("/api/v1/result-tree")
    def tree() -> Dict[str, Any]:
        return branch_schema.dump(test_runner.result_tree)

    @socketio.on("run test")
    def run_test(nodeid):
        LOGGER.info("Running test: %s", nodeid)
        test_runner.run_tests(nodeid)

    @socketio.on("connect")
    def connect():
        LOGGER.debug("Client connected")

    @socketio.on("disconnect")
    def disconnect():
        LOGGER.debug("Client disconnected")

    return app, socketio
