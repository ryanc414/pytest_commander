"""Unit tests for the HTTP API."""
import json
import os

import pytest

from pytest_web_ui import api


@pytest.fixture
def clients():
    """Setup and yield flask and socketIO test clients."""
    directory = os.path.join(os.path.dirname(__file__), os.pardir, "pytest_examples",)
    app, socketio = api.build_app(directory)
    app.config["TESTING"] = True
    with app.test_client() as client:
        socket_client = socketio.test_client(app, flask_test_client=client)
        yield client, socket_client


def test_report_skeleton(clients):
    """Test that the report skeleton is correctly returned after init."""
    client, _ = clients
    json_filepath = os.path.join(
        os.path.dirname(__file__), os.pardir, "test_data", "result_tree_skeleton.json"
    )

    rsp = client.get("/api/v1/result-tree")
    assert rsp.status_code == 200
    rsp_json = rsp.get_json()

    # Uncomment to update the serialization snapshot.
    # with open(json_filepath, "w") as f:
    #     json.dump(rsp_json, f, indent=2)

    with open(json_filepath) as f:
        expected_serialization = json.load(f)

    assert rsp_json == expected_serialization


def test_run_test(clients):
    _, socket_client = clients
    socket_client.emit("run test", "pytest_examples/test_a.py::test_one")
    rcvd = socket_client.get_received()
    assert len(rcvd) == 2
    json_filepath = os.path.join(
        os.path.dirname(__file__), os.pardir, "test_data", "test_run_update.json"
    )

    # Uncomment to update expected JSON.
    # with open(json_filepath, "w") as f:
    #     json.dump(rcvd, f, indent=2)

    with open(json_filepath) as f:
        expected_rcvd = json.load(f)

    assert rcvd == expected_rcvd
