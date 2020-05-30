import asyncio
import collections
import inspect
from contextlib import suppress
from functools import partial, wraps
from pathlib import Path
from typing import (
    Callable,
    Dict,
    Union,
    Optional,
    Any,
    Generator,
    AsyncGenerator,
    List,
    Iterable,
    Mapping,
    Tuple,
    Collection,
)

from dataclasses import dataclass, field

from ward.models import WardMeta, Scope


@dataclass
class Fixture:
    fn: Callable
    gen: Union[Generator, AsyncGenerator] = None
    resolved_val: Any = None

    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        return self._id == other._id

    @property
    def _id(self):
        return self.__class__, self.name, self.path, self.line_number

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
    def module_name(self):
        return self.fn.__module__

    @property
    def qualified_name(self) -> str:
        name = self.name or ""
        return f"{self.module_name}.{name}"

    @property
    def line_number(self) -> int:
        return inspect.getsourcelines(self.fn)[1]

    @property
    def is_generator_fixture(self):
        return inspect.isgeneratorfunction(inspect.unwrap(self.fn))

    @property
    def is_async_generator_fixture(self):
        return inspect.isasyncgenfunction(inspect.unwrap(self.fn))

    @property
    def is_coroutine_fixture(self):
        return inspect.iscoroutinefunction(inspect.unwrap(self.fn))

    def deps(self):
        return inspect.signature(self.fn).parameters

    def parents(self) -> List["Fixture"]:
        """
        Return the parent fixtures of this fixture, as a list of Fixtures.
        """
        return [Fixture(par.default) for par in self.deps().values()]

    def teardown(self):
        # Suppress because we can't know whether there's more code
        # to execute below the yield.
        with suppress(RuntimeError, StopIteration, StopAsyncIteration):
            if self.is_generator_fixture and self.gen:
                next(self.gen)
            elif self.is_async_generator_fixture and self.gen:
                awaitable = self.gen.__anext__()
                asyncio.get_event_loop().run_until_complete(awaitable)


FixtureKey = str
TestId = str
ScopeKey = Union[TestId, Path, Scope]
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


_DEFINED_FIXTURES = []


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

    _DEFINED_FIXTURES.append(Fixture(func))

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


def is_fixture(obj: Any) -> bool:
    """
    Returns True if and only if the object is a fixture function
    (it would be False for a Fixture instance,
    but True for the underlying function inside it).
    """
    return hasattr(obj, "ward_meta") and obj.ward_meta.is_fixture


_TYPE_FIXTURE_TO_FIXTURES = Mapping[Fixture, Collection[Fixture]]


def fixture_parents_and_children(
    fixtures: Iterable[Fixture],
) -> Tuple[_TYPE_FIXTURE_TO_FIXTURES, _TYPE_FIXTURE_TO_FIXTURES]:
    """
    Given an iterable of Fixtures, produce two dictionaries:
    the first maps each fixture to its parents (the fixtures it depends on);
    the second maps each fixture to its children (the fixtures that depend on it).
    """
    fixtures_to_parents = {fixture: fixture.parents() for fixture in fixtures}

    # not a defaultdict, because we want to have empty entries if no parents when we return
    fixtures_to_children = {fixture: [] for fixture in fixtures}
    for fixture, parents in fixtures_to_parents.items():
        for parent in parents:
            fixtures_to_children[parent].append(fixture)

    return fixtures_to_parents, fixtures_to_children
