"""Classes to help interacting with pytest nodeids."""
from __future__ import annotations

import collections
import os
from typing import List, Any

NodeidFragment = collections.namedtuple("NodeidFragment", ["val", "is_path"])


class Nodeid:
    """Wraps a nodeid string and helps with splitting into components."""

    _PATH_SEP = "/"
    _NONPATH_SEP = "::"

    def __init__(self, raw_nodeid: str, fragments: List[NodeidFragment]):
        self._raw_nodeid = raw_nodeid
        self._fragments = fragments

    @classmethod
    def from_string(cls, raw_nodeid: str) -> Nodeid:
        if not raw_nodeid:
            return cls("", [])

        raw_components = raw_nodeid.split("::")
        path_components = [
            NodeidFragment(val=frag, is_path=True)
            for frag in raw_components[0].split("/")
        ]
        nonpath_components = [
            NodeidFragment(val=frag, is_path=False) for frag in raw_components[1:]
        ]
        fragments = path_components + nonpath_components
        return cls(raw_nodeid, fragments)

    @classmethod
    def from_fragments(cls, fragments: List[NodeidFragment]) -> Nodeid:
        if not fragments:
            return cls("", [])

        str_components = [fragments[0].val]
        for frag in fragments[1:]:
            separator = cls._PATH_SEP if frag.is_path else cls._NONPATH_SEP
            str_components.append(separator)
            str_components.append(frag.val)

        raw_nodeid = "".join(str_components)
        return cls(raw_nodeid, fragments)

    @classmethod
    def from_path(cls, path: str, root_dir: str) -> Nodeid:
        if not path.startswith(root_dir):
            raise ValueError(
                f"path {path} does not appear to be within root dir {root_dir}"
            )

        return cls.from_string(path[len(root_dir) + 1 :])

    def __iter__(self):
        return iter(self._fragments)

    def __str__(self):
        return self._raw_nodeid

    def __eq__(self, other: Any):
        if isinstance(other, Nodeid):
            return str(self) == str(other)
        return False

    @property
    def raw(self) -> str:
        return self._raw_nodeid

    @property
    def fragments(self) -> List[NodeidFragment]:
        return self._fragments

    @property
    def fspath(self):
        return self._raw_nodeid.replace("/", os.sep)

    def append(self, fragment: NodeidFragment) -> Nodeid:
        """Returns a new nodeid with the new fragment appended."""
        return Nodeid.from_fragments(self._fragments + [fragment])

    @property
    def parent(self) -> Nodeid:
        """Returns the parent nodeid."""
        if not self._fragments:
            raise RuntimeError("empty nodeid has no parents, like batman")
        return Nodeid.from_fragments(self._fragments[:-1])

    @property
    def short_id(self) -> str:
        return self.fragments[-1].val


EMPTY_NODEID = Nodeid("", [])
