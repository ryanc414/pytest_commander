"""Unit tests for the HTTP API."""
import json
from unittest import mock
import os

import eventlet
import pytest

from pytest_commander import api

EXAMPLES_DIR = os.path.relpath(
    os.path.join(os.path.dirname(__file__), os.pardir, "pytest_examples")
)


@pytest.fixture
def clients():
    """Setup and yield flask and socketIO test clients."""
    app, socketio, _ = api.build_app(EXAMPLES_DIR, False)
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
    socket_client.emit("run test", "test_a.py::test_one")

    total_rcvd = []
    while len(total_rcvd) < 3:
        rcvd = socket_client.get_received()
        eventlet.sleep(0.1)
        total_rcvd.extend(rcvd)

    json_filepath = os.path.join(
        os.path.dirname(__file__), os.pardir, "test_data", "test_run_update.json"
    )

    # Uncomment to update expected JSON.
    # with open(json_filepath, "w") as f:
    #     json.dump(total_rcvd, f, indent=2)

    with open(json_filepath) as f:
        expected_rcvd = json.load(f)

    assert total_rcvd == expected_rcvd


@mock.patch("subprocess.check_call")
@mock.patch("subprocess.Popen")
def test_environment(mock_popen, mock_check_call, clients):
    _, socket_client = clients

    socket_client.emit("start env", "")
    rcvd = socket_client.get_received()
    assert len(rcvd) == 1
    mock_popen.assert_called_once_with(
        ["docker-compose", "-f", "pytest_examples/docker-compose.yml", "up"]
    )

    socket_client.emit("stop env", "")
    rcvd = []
    while len(rcvd) < 2:
        rcvd.extend(socket_client.get_received())
    mock_check_call.assert_called_once_with(
        ["docker-compose", "-f", "pytest_examples/docker-compose.yml", "down"]
    )

