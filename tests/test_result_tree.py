"""Unit tests for the result_tree module"""

import collections
import json
import os

from pytest_web_ui import result_tree

SessionItem = collections.namedtuple("SessionItem", ["nodeid"])


def test_build_tree():
    items = [
        SessionItem(nodeid)
        for nodeid in [
            "path/to/test_a.py::TestSuite::test_one",
            "path/to/test_a.py::TestSuite::test_two",
            "path/to/test_a.py::test_one",
            "path/to/test_a.py::test_two",
        ]
    ]
    tree, _ = result_tree.build_from_items(items, "path")
    assert isinstance(tree, result_tree.BranchNode)
    serializer = result_tree.BranchNodeSchema()
    serialized_tree = serializer.dump(tree)

    json_filepath = os.path.join(
        os.path.dirname(__file__), os.pardir, "test_data", "test_build_tree.json"
    )

    # Uncomment to update snapshot.
    # with open(json_filepath, "w") as f:
    #     json.dump(serialized_tree, f, indent=2)

    with open(json_filepath) as f:
        expected_serialization = json.load(f)

    assert serialized_tree == expected_serialization

