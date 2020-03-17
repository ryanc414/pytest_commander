"""Unit tests for the HTTP API."""
import json
import os

import pytest

from pytest_web_ui import api


@pytest.fixture
def client():
    directory = os.path.join(os.path.dirname(__file__), os.pardir, "pytest_examples",)
    app = api.build_app(directory)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_report_skeleton(client):
    json_filepath = os.path.join(
        os.path.dirname(__file__), os.pardir, "test_data", "result_tree_skeleton.json"
    )

    with open(json_filepath) as f:
        expected_serialization = json.load(f)

    rsp = client.get("/api/v1/result-tree")
    assert rsp.status_code == 200
    rsp_json = rsp.get_json()
    assert rsp_json == expected_serialization
