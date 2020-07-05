import time

import pytest
import requests


def test_one():
    assert 1 > 0


def test_two():
    assert 1 < 0


@pytest.fixture
def http_server():
    """Await the HTTP server to be ready."""
    for i in range(1000):
        rsp = requests.get("http://localhost:5678")
        if rsp.status_code == 200:
            break
        time.sleep(0.1)
    else:
        raise RuntimeError("timed out waiting for HTTP server")


def test_http_service(http_server):
    """
    Test hitting the HTTP echo server. This is expected to be started
    automatically from to the docker-compose.yml file.
    """
    rsp = requests.get("http://localhost:5678")
    rsp.raise_for_status()
    assert rsp.text == "hello world\n"
