"""HTTP API for PyTest runner."""
from typing import Dict, Any
import flask
from . import runner
from . import result_tree


def build_app(directory: str) -> flask.Flask:
    """Build a Flask app to serve the API and static files."""
    app = flask.Flask(__name__)
    test_runner = runner.PyTestRunner(directory)
    tree_schema = result_tree.BranchNodeSchema()

    @app.route("/api/v1/result-tree")
    def tree() -> Dict[str, Any]:
        return tree_schema.dump(test_runner.result_tree)

    return app
