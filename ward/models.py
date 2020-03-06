from dataclasses import dataclass
from enum import Enum
from inspect import BoundArguments
from pathlib import Path
from typing import List, Optional

from ward.errors import FixtureError


class Scope(Enum):
    Test = "test"
    Module = "module"
    Global = "global"

    @classmethod
    def from_str(cls, scope_str: str) -> "Scope":
        try:
            return cls[scope_str.title()]
        except (AttributeError, KeyError) as err:
            raise FixtureError(f"Invalid fixture scope: '{scope_str}'") from err


@dataclass
class Marker:
    name: str


@dataclass
class SkipMarker(Marker):
    name: str = "SKIP"
    reason: Optional[str] = None


@dataclass
class XfailMarker(Marker):
    name: str = "XFAIL"
    reason: Optional[str] = None


@dataclass
class WardMeta:
    marker: Optional[Marker] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_fixture: bool = False
    scope: Scope = Scope.Test
    bound_args: Optional[BoundArguments] = None
    path: Optional[Path] = None
