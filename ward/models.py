from dataclasses import dataclass
from enum import Enum
from inspect import BoundArguments
from pathlib import Path
from typing import Callable, List, Optional, Union

from ward._errors import FixtureError

__all__ = ["Scope", "SkipMarker", "XfailMarker", "ExitCode", "CollectionMetadata"]


class Scope(Enum):
    """
    The scope of a fixture defines how long it will be cached for.

    Attributes:
        Test: A test-scoped fixture will be called each time a dependent test runs.
        Module: A module-scoped fixture will be called at most once per test module.
        Global: A global-scoped fixture will be called at most once per invocation of ``ward``.
    """

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
    """
    Marker that gets attached to a test (via CollectionMetadata) to indicate it should be skipped.
    """

    name: str = "SKIP"


@dataclass
class XfailMarker(Marker):
    """
    Marker that gets attached to a test (via CollectionMetadata) to indicate that we expect it to fail.
    """

    name: str = "XFAIL"


@dataclass
class CollectionMetadata:
    """
    Attached to tests and fixtures during the collection phase for later use.
    """

    marker: Optional[Marker] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_fixture: bool = False
    scope: Scope = Scope.Test
    bound_args: Optional[BoundArguments] = None
    path: Optional[Path] = None


class ExitCode(Enum):
    """
    Enumeration of the possible exit codes that Ward can exit with.
    """

    SUCCESS = 0
    FAILED = 1
    ERROR = 2
    NO_TESTS_FOUND = 3

    @property
    def clean_name(self):
        return self.name.replace("_", " ")
