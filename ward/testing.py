import functools
import inspect
from collections import defaultdict
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Dict, List, Optional

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


def skip(func_or_reason=None, *, reason: str = None):
    if func_or_reason is None:
        return functools.partial(skip, reason=reason)

    if isinstance(func_or_reason, str):
        return functools.partial(skip, reason=func_or_reason)

    func = func_or_reason
    func.ward_meta = WardMeta(marker=SkipMarker(reason=reason))

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def xfail(func=None, *, reason: str = None):
    if func is None:
        return functools.partial(xfail, reason=reason)

    func.ward_meta = WardMeta(marker=XfailMarker(reason=reason))

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@dataclass
class Test:
    fn: Callable
    module_name: str
    marker: Optional[Marker] = None
    description: Optional[str] = None

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)

    @property
    def name(self):
        return self.fn.__name__

    @property
    def qualified_name(self):
        return f"{self.module_name}.{self.name}"

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


# Tests declared with the name _, and with the @test decorator
# have to be stored in here, so that they can later be retrieved.
# They cannot be retrieved directly from the module due to name
# clashes. When we're later looking for tests inside the module,
# we can retrieve any anonymous tests from this dict.
anonymous_tests: Dict[str, List[Test]] = defaultdict(list)


def test(description: str):
    def decorator_test(func):
        if func.__name__ == "_":
            mod_name = func.__module__
            anonymous_tests[mod_name].append(Test(
                fn=func,
                module_name=mod_name,
                description=description,
                marker=getattr(func, "ward_meta", WardMeta()).marker,
            ))

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator_test
