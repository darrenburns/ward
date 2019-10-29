import functools
import inspect
from collections import defaultdict
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Callable, Dict, List, Optional, Any

from ward.fixtures import Fixture, FixtureCache, FixtureExecutionError, get_cache_key_for_func
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
    fixture_cache: FixtureCache = field(default_factory=FixtureCache)
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

    def resolve_fixtures(self) -> Dict[str, Fixture]:
        """
        Resolve fixtures and return the resultant BoundArguments
        formed by partially binding resolved fixture values.
        Resolved values will be stored in fixture_cache, accessible
        using the fixture cache key (See `fixtures.get_cache_key_for_func`).
        """
        signature = inspect.signature(self.fn)
        default_binding = signature.bind_partial()
        if not self.has_deps():
            return {}

        default_binding.apply_defaults()

        resolved_args: Dict[str, Fixture] = {}
        for name, arg in default_binding.arguments.items():
            if hasattr(arg, "ward_meta") and arg.ward_meta.is_fixture:
                resolved = self._resolve_single_fixture(arg)
            else:
                resolved = arg
            resolved_args[name] = resolved
        return resolved_args

    def _resolve_single_fixture(self, fixture: Callable) -> Fixture:
        key = get_cache_key_for_func(fixture)
        if key in self.fixture_cache:
            return self.fixture_cache[key]

        deps = inspect.signature(fixture)
        has_deps = len(deps.parameters) > 0
        f = Fixture(key, fixture)
        is_generator = inspect.isgeneratorfunction(inspect.unwrap(fixture))
        if not has_deps:
            try:
                if is_generator:
                    f.gen = fixture()
                    f.resolved_val = next(f.gen)
                else:
                    f.resolved_val = fixture()
            except Exception as e:
                raise FixtureExecutionError(
                    f"Unable to execute fixture '{f.key}'"
                ) from e
            self.fixture_cache.cache_fixture(f)
            return f

        signature = inspect.signature(fixture)
        children_defaults = signature.bind_partial()
        children_defaults.apply_defaults()
        children_resolved = {}
        for name, child_fixture in children_defaults.arguments.items():
            child_resolved = self._resolve_single_fixture(child_fixture)
            children_resolved[name] = child_resolved
        try:
            if is_generator:
                f.gen = fixture(**self._resolve_fixture_values(children_resolved))
                f.resolved_val = next(f.gen)
            else:
                f.resolved_val = fixture(**self._resolve_fixture_values(children_resolved))
        except Exception as e:
            raise FixtureExecutionError(
                f"Unable to execute fixture '{f.key}'"
            ) from e
        self.fixture_cache.cache_fixture(f)
        return f

    def _resolve_fixture_values(self, fixture_dict: Dict[str, Fixture]) -> Dict[str, Any]:
        return {
            key: f.resolved_val for key, f in fixture_dict.items()
        }

    def teardown_fixtures_in_cache(self):
        self.fixture_cache.teardown_all()


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
