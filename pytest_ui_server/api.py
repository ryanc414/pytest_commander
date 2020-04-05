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

        def update_callback(result: result_tree.Node):
            parents_slice, parent_node = _serialize_parents_slice(result)

            if isinstance(result, result_tree.BranchNode):
                serialized_result = shallow_branch_schema.dump(result)
                parent_node["child_branches"] = {result.nodeid: serialized_result}
            elif isinstance(result, result_tree.LeafNode):
                serialized_result = leaf_schema.dump(result)
                parent_node["child_leaves"] = {result.nodeid: serialized_result}
            else:
                raise TypeError(f"Unexpected result type: {type(result)}")

            LOGGER.debug("Sending update for nodeid %s", result.nodeid)
            socketio.emit("update", parents_slice)

        test_runner.run_tests(nodeid, update_callback)

    @socketio.on("connect")
    def connect():
        LOGGER.debug("Client connected")

    @socketio.on("disconnect")
    def disconnect():
        LOGGER.debug("Client disconnected")

    def _serialize_parents_slice(
        result_node: result_tree.Node,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Serialize a slice of the tree from root to the given result node."""
        serialized_root = shallow_branch_schema._serialize(test_runner.result_tree)
        curr_serialized_node = serialized_root
        curr_node = test_runner.result_tree

        for uid in result_node.parent_nodeids:
            curr_node = curr_node.child_branches[uid]
            serialized_child = shallow_branch_schema._serialize(curr_node)
            curr_serialized_node["child_branches"] = {uid: serialized_child}
            curr_serialized_node = serialized_child

        return serialized_root, curr_serialized_node

    return app, socketio
