import functools
import inspect
from collections import defaultdict
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Dict, List, Optional, Any

from ward.fixtures import Fixture, FixtureCache, FixtureExecutionError
from ward.models import Marker, SkipMarker, XfailMarker, WardMeta


def skip(func_or_reason=None, *, reason: str = None):
    if func_or_reason is None:
        return functools.partial(skip, reason=reason)

    if isinstance(func_or_reason, str):
        return functools.partial(skip, reason=func_or_reason)

    func = func_or_reason
    marker = SkipMarker(reason=reason)
    if hasattr(func, "ward_meta"):
        func.ward_meta.marker = marker
    else:
        func.ward_meta = WardMeta(marker=marker)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def xfail(func_or_reason=None, *, reason: str = None):
    if func_or_reason is None:
        return functools.partial(xfail, reason=reason)

    if isinstance(func_or_reason, str):
        return functools.partial(xfail, reason=func_or_reason)

    func = func_or_reason
    marker = XfailMarker(reason=reason)
    if hasattr(func, "ward_meta"):
        func.ward_meta.marker = marker
    else:
        func.ward_meta = WardMeta(marker=marker)

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
        name = self.name or ""
        return f"{self.module_name}.{name}"

    @property
    def line_number(self):
        return inspect.getsourcelines(self.fn)[1]

    def deps(self) -> MappingProxyType:
        return inspect.signature(self.fn).parameters

    def has_deps(self) -> bool:
        return len(self.deps()) > 0

    def resolve_args(self, fixture_cache: FixtureCache) -> Dict[str, Fixture]:
        """Resolve fixture that has been injected into this test"""
        if not self.has_deps():
            return {}

        # Construct a dict of kwargs to pass into the test when it's called
        resolved_args = {}
        for fixture_name in self.deps():
            fixture = fixture_cache[fixture_name]
            resolved_arg = fixture.resolve(fixture_cache)
            resolved_args[fixture_name] = resolved_arg

        return resolved_args

    def resolve_fixtures(self) -> inspect.BoundArguments:
        """
        Resolve fixtures and return the resultant BoundArguments
        formed by partially binding resolved fixture values.
        """
        signature = inspect.signature(self.fn)
        default_binding = signature.bind_partial()
        if not self.has_deps():
            return default_binding

        default_binding.apply_defaults()

        # TODO: Right now, we'll keep the cache on a per-test
        #  basis since we don't do fixture scoping, but we can
        #  always pull it further up in scope if necessary.
        fixture_cache = FixtureCache()

        resolved_args: Dict[str, Fixture] = {}
        for name, arg in default_binding.arguments.items():
            if hasattr(arg, "ward_meta") and arg.ward_meta.is_fixture:
                resolved = self._resolve_single_fixture(arg, fixture_cache)
            else:
                resolved = arg
            resolved_args[name] = resolved

        return signature.bind_partial(**resolved_args)

    def _resolve_single_fixture(self, fixture: Callable, cache: FixtureCache) -> Fixture:
        deps = inspect.signature(fixture)
        has_deps = len(deps.parameters) > 0
        key = self._get_cache_key(fixture)
        f = Fixture(key, fixture)
        if not has_deps:
            try:
                if inspect.isgeneratorfunction(fixture):
                    f.gen = fixture()
                    f.resolved_val = next(f.gen)
                else:
                    f.resolved_val = fixture()
            except Exception as e:
                raise FixtureExecutionError(
                    f"Unable to execute fixture '{f.key}'"
                ) from e
            cache.cache_fixture(f)
            return f

        signature = inspect.signature(fixture)
        children_defaults = signature.bind_partial()
        children_defaults.apply_defaults()
        children_resolved = {}
        for name, child_fixture in children_defaults.arguments.items():
            child_resolved = self._resolve_single_fixture(child_fixture, cache)
            children_resolved[name] = child_resolved
        try:
            if inspect.isgeneratorfunction(fixture):
                f.gen = fixture(**self._resolve_fixture_values(children_resolved))
                f.resolved_val = next(f.gen)
            else:
                f.resolved_val = fixture(**self._resolve_fixture_values(children_resolved))
        except Exception as e:
            raise FixtureExecutionError(
                f"Unable to execute fixture '{f.key}'"
            ) from e

        return f

    def _get_cache_key(self, fixture: Callable):
        path = inspect.getfile(fixture)
        name = fixture.__name__
        return f"{path}::{name}"

    def _resolve_fixture_values(self, fixture_dict: Dict[str, Fixture]) -> Dict[str, Any]:
        return {
            key: f.resolved_val for key, f in fixture_dict.items()
        }


# TODO: Remove this comment
# if not self.deps():
#     try:
#         if self.is_generator_fixture:
#             self.gen = self.fn()
#             self.resolved_val = next(self.gen)
#         else:
#             self.resolved_val = self.fn()
#     except Exception as e:
#         raise FixtureExecutionError(
#             f"Unable to execute fixture '{self.key}'"
#         ) from e
#     fix_cache.cache_fixture(self)
#     return self
#
# # Otherwise, we have to find the child fixture vals, and call self
# children = self.deps()
# children_resolved = []
# for child in children:
#     child_fixture = fix_cache[child].resolve(fix_cache)
#     children_resolved.append(child_fixture)
#
# # We've resolved the values of all child fixtures
# try:
#     child_resolved_vals = [child.resolved_val for child in children_resolved]
#     if self.is_generator_fixture:
#         self.gen = self.fn(*child_resolved_vals)
#         self.resolved_val = next(self.gen)
#     else:
#         self.resolved_val = self.fn(*child_resolved_vals)
# except Exception as e:
#     raise FixtureExecutionError(
#         f"Unable to execute fixture '{self.key}'"
#     ) from e
#
# fix_cache.cache_fixture(self)
# return self


# Tests declared with the name _, and with the @test decorator
# have to be stored in here, so that they can later be retrieved.
# They cannot be retrieved directly from the module due to name
# clashes. When we're later looking for tests inside the module,
# we can retrieve any anonymous tests from this dict.
anonymous_tests: Dict[str, List[Callable]] = defaultdict(list)


def test(description: str):
    def decorator_test(func):
        if func.__name__ == "_":
            mod_name = func.__module__
            if hasattr(func, "ward_meta"):
                func.ward_meta.description = description
            else:
                func.ward_meta = WardMeta(description=description)
            anonymous_tests[mod_name].append(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator_test
