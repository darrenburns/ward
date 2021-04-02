from dataclasses import dataclass
from enum import Enum
from inspect import BoundArguments
from pathlib import Path
from typing import List, Optional, Union, Callable

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
    reason: Optional[str] = None
    when: Union[bool, Callable] = True

    @property
    def active(self):
        try:
            return self.when()
        except TypeError:
            return self.when


@dataclass
class SkipMarker(Marker):
    name: str = "SKIP"


@dataclass
class XfailMarker(Marker):
    name: str = "XFAIL"


@dataclass
class WardMeta:
    marker: Optional[Marker] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_fixture: bool = False
    scope: Scope = Scope.Test
    bound_args: Optional[BoundArguments] = None
    path: Optional[Path] = None
