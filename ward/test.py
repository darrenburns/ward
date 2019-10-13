import inspect
from dataclasses import dataclass
from enum import Enum, auto
from types import MappingProxyType, ModuleType
from typing import Any, Callable, Dict

from ward.fixtures import FixtureRegistry, Fixture


class WardMarker(Enum):
    NONE = auto()
    SKIP = auto()
    FLAKY = auto()


def skip(func):
    func.ward_marker = WardMarker.SKIP
    return func


@dataclass
class Test:
    fn: Callable
    module: ModuleType
    marker: WardMarker = WardMarker.NONE

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
