import inspect
from contextlib import suppress
from dataclasses import dataclass, field
from functools import partial, wraps
from pathlib import Path
from typing import Callable, Dict, Union, Optional, Any, Generator

from ward.models import WardMeta, Scope


@dataclass
class Fixture:
    fn: Callable
    gen: Generator = None
    resolved_val: Any = None

    @property
    def key(self) -> str:
        path = self.path
        name = self.name
        return f"{path}::{name}"

    @property
    def scope(self) -> Scope:
        return getattr(self.fn, "ward_meta").scope

    @property
    def name(self):
        return self.fn.__name__

    @property
    def path(self):
        return self.fn.ward_meta.path

    @property
    def is_generator_fixture(self):
        return inspect.isgeneratorfunction(inspect.unwrap(self.fn))

    def deps(self):
        return inspect.signature(self.fn).parameters

    def teardown(self):
        # Suppress because we can't know whether there's more code
        # to execute below the yield.
        with suppress(StopIteration, RuntimeError):
            if self.is_generator_fixture and self.gen:
                next(self.gen)


FixtureKey = str
TestId = str
ModulePath = str
ScopeKey = Union[TestId, ModulePath, Scope]
ScopeCache = Dict[Scope, Dict[ScopeKey, Dict[FixtureKey, Fixture]]]


def _scope_cache_factory():
    return {scope: {} for scope in Scope}


@dataclass
class FixtureCache:
    """
    A collection of caches, each storing data for a different scope.

    When a fixture is resolved, it is stored in the appropriate cache given
    the scope of the fixture.

    A lookup into this cache is a 3 stage process:

    Scope -> ScopeKey -> FixtureKey

    The first 2 lookups (Scope and ScopeKey) let us determine:
        e.g. has a test-scoped fixture been cached for the current test?
        e.g. has a module-scoped fixture been cached for the current test module?

    The final lookup lets us retrieve the actual fixture given a fixture key.
    """

    _scope_cache: ScopeCache = field(default_factory=_scope_cache_factory)

    def _get_subcache(self, scope: Scope) -> Dict[str, Any]:
        return self._scope_cache[scope]

    def get_fixtures_at_scope(
        self, scope: Scope, scope_key: ScopeKey
    ) -> Dict[FixtureKey, Fixture]:
        subcache = self._get_subcache(scope)
        if scope_key not in subcache:
            subcache[scope_key] = {}
        return subcache.get(scope_key)

    def cache_fixture(self, fixture: Fixture, scope_key: ScopeKey):
        """
        Cache a fixture at the appropriate scope for the given test.
        """
        fixtures = self.get_fixtures_at_scope(fixture.scope, scope_key)
        fixtures[fixture.key] = fixture

    def teardown_fixtures_for_scope(self, scope: Scope, scope_key: ScopeKey):
        fixture_dict = self.get_fixtures_at_scope(scope, scope_key)
        fixtures = list(fixture_dict.values())
        for fixture in fixtures:
            with suppress(RuntimeError, StopIteration):
                fixture.teardown()
            del fixture_dict[fixture.key]

    def teardown_global_fixtures(self):
        self.teardown_fixtures_for_scope(Scope.Global, Scope.Global)

    def contains(self, fixture: Fixture, scope: Scope, scope_key: ScopeKey) -> bool:
        fixtures = self.get_fixtures_at_scope(scope, scope_key)
        return fixture.key in fixtures

    def get(
        self, fixture_key: FixtureKey, scope: Scope, scope_key: ScopeKey
    ) -> Fixture:
        fixtures = self.get_fixtures_at_scope(scope, scope_key)
        return fixtures.get(fixture_key)


def fixture(func=None, *, scope: Optional[Union[Scope, str]] = Scope.Test):
    if not isinstance(scope, Scope):
        scope = Scope.from_str(scope)

    if func is None:
        return partial(fixture, scope=scope)

    # By setting is_fixture = True, the framework will know
    # that if this fixture is provided as a default arg, it
    # is responsible for resolving the value.
    path = Path(inspect.getfile(func)).absolute()
    if hasattr(func, "ward_meta"):
        func.ward_meta.is_fixture = True
        func.ward_meta.path = path
    else:
        func.ward_meta = WardMeta(is_fixture=True, scope=scope, path=path)

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def using(*using_args, **using_kwargs):
    def decorator_using(func):
        signature = inspect.signature(func)
        bound_args = signature.bind_partial(*using_args, **using_kwargs)
        if hasattr(func, "ward_meta"):
            func.ward_meta.bound_args = bound_args
        else:
            func.ward_meta = WardMeta(bound_args=bound_args)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator_using
