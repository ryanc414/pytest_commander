import requests


def test_one():
    assert 1 > 0


def test_two():
    assert 1 < 0


def test_http_service():
    """
    Test hitting the HTTP echo server. This is expected to be started
    automatically from to the docker-compose.yml file.
    """
    rsp = requests.get("http://localhost:5678")
    rsp.raise_for_status()
    assert rsp.text == "hello world\n"
