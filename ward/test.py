import functools
import inspect
from dataclasses import dataclass
from types import MappingProxyType, ModuleType
from typing import Callable, Dict, Optional

from ward.fixtures import Fixture, FixtureRegistry


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


def skip(func=None, *, reason: str = None):
    if func is None:
        return functools.partial(skip, reason=reason)

    func.ward_meta = WardMeta(marker=SkipMarker(reason=reason))

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def xfail(func=None, *, reason: str = None):
    if func is None:
        return functools.partial(xfail, reason=reason)

    func.ward_meta = WardMeta(marker=SkipMarker(reason=reason))

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@dataclass
class Test:
    fn: Callable
    module: ModuleType
    marker: Optional[Marker] = None

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)

    @property
    def name(self):
        return self.fn.__name__

    @property
    def qualified_name(self):
        return f"{self.module.__name__}.{self.name}"

    def deps(self) -> MappingProxyType:
        return inspect.signature(self.fn).parameters

    def has_deps(self) -> bool:
        return len(self.deps()) > 0

    def resolve_args(self, fixture_registry: FixtureRegistry) -> Dict[str, Fixture]:
        """Resolve fixture that has been injected into this test"""
        if not self.has_deps():
            return {}

        # Construct a dict of kwargs to pass into the test when it's called
        resolved_args = {}
        for fixture_name in self.deps():
            fixture = fixture_registry[fixture_name]
            resolved_arg = fixture.resolve(fixture_registry)
            resolved_args[fixture_name] = resolved_arg

        return resolved_args
