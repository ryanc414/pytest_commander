"""Classes to help interacting with pytest nodeids."""
import collections
import enum
import os
import re
from typing import List, Any

NodeidFragment = collections.namedtuple("NodeidFragment", ["val", "type"])


class FragmentTypes(enum.Enum):

    PATH_COMPONENT = 1
    METHOD_COMPONENT = 2
    PARAMETER = 3


class Nodeid:
    """Wraps a nodeid string and helps with splitting into components."""

    _PATH_SEP = "/"
    _NONPATH_SEP = "::"
    _PARAM_OPENER = "["
    _PARAM_CLOSER = "]"
    _PARAM_RX = re.compile(r"(.*)\[(.*)\]")

    def __init__(self, raw_nodeid: str, fragments: List[NodeidFragment]):
        self._raw_nodeid = raw_nodeid
        self._fragments = fragments

    @classmethod
    def from_string(cls, raw_nodeid: str) -> "Nodeid":
        if not raw_nodeid:
            return cls("", [])

        raw_components = raw_nodeid.split("::")
        path_components = [
            NodeidFragment(val=frag, type=FragmentTypes.PATH_COMPONENT)
            for frag in raw_components[0].split("/")
        ]
        nonpath_components = [
            NodeidFragment(val=frag, type=FragmentTypes.METHOD_COMPONENT)
            for frag in raw_components[1:]
        ]
        fragments = path_components + nonpath_components
        match = cls._PARAM_RX.match(fragments[-1].val)
        if match:
            fragments = fragments[:-1] + [
                NodeidFragment(val=match.group(1), type=FragmentTypes.METHOD_COMPONENT),
                NodeidFragment(val=match.group(2), type=FragmentTypes.PARAMETER),
            ]

        return cls(raw_nodeid, fragments)

    @classmethod
    def from_fragments(cls, fragments: List[NodeidFragment]) -> "Nodeid":
        if not fragments:
            return cls("", [])

        str_components = [fragments[0].val]
        for frag in fragments[1:]:
            if frag.type == FragmentTypes.PATH_COMPONENT:
                str_components.append(cls._PATH_SEP)
                str_components.append(frag.val)
            elif frag.type == FragmentTypes.METHOD_COMPONENT:
                str_components.append(cls._NONPATH_SEP)
                str_components.append(frag.val)
            elif frag.type == FragmentTypes.PARAMETER:
                str_components.append(cls._PARAM_OPENER)
                str_components.append(frag.val)
                str_components.append(cls._PARAM_CLOSER)
            else:
                raise ValueError(
                    f"unexpected fragment type {frag.type} for element {frag.val}"
                )

        raw_nodeid = "".join(str_components)
        return cls(raw_nodeid, fragments)

    @classmethod
    def from_path(cls, path: str, root_dir: str) -> "Nodeid":
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

    def append(self, fragment: NodeidFragment) -> "Nodeid":
        """Returns a new nodeid with the new fragment appended."""
        return Nodeid.from_fragments(self._fragments + [fragment])

    @property
    def parent(self) -> "Nodeid":
        """Returns the parent nodeid."""
        if not self._fragments:
            raise RuntimeError("empty nodeid has no parents, like batman")
        return Nodeid.from_fragments(self._fragments[:-1])

    @property
    def short_id(self) -> str:
        return self.fragments[-1].val


EMPTY_NODEID = Nodeid("", [])
