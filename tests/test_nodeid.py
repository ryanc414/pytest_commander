"""Unit tests for nodeid module."""
from pytest_commander import nodeid


def test_nodeid():
    raw_nodeid = "path/to/test_a.py::TestSuite::test_method[1]"
    node_id = nodeid.Nodeid.from_string(raw_nodeid)

    assert len(node_id.fragments) == 6

    assert node_id.fragments[0].val == "path"
    assert node_id.fragments[0].type == nodeid.FragmentTypes.PATH_COMPONENT
    assert node_id.fragments[1].val == "to"
    assert node_id.fragments[1].type == nodeid.FragmentTypes.PATH_COMPONENT
    assert node_id.fragments[2].val == "test_a.py"
    assert node_id.fragments[2].type == nodeid.FragmentTypes.PATH_COMPONENT
    assert node_id.fragments[3].val == "TestSuite"
    assert node_id.fragments[3].type == nodeid.FragmentTypes.METHOD_COMPONENT
    assert node_id.fragments[4].val == "test_method"
    assert node_id.fragments[4].type == nodeid.FragmentTypes.METHOD_COMPONENT
    assert node_id.fragments[5].val == "1"
    assert node_id.fragments[5].type == nodeid.FragmentTypes.PARAMETER

    assert str(node_id) == raw_nodeid
