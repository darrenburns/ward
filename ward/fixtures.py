import inspect
from contextlib import suppress
from dataclasses import dataclass, field
from functools import partial, wraps
from typing import Callable, Dict, Union, Optional, List

from ward.models import WardMeta, Scope


@dataclass
class Fixture:
    def __init__(
        self,
        fn: Callable,
        last_resolved_module_name: Optional[str] = None,
        last_resolved_test_id: Optional[str] = None,
    ):
        self.fn = fn
        self.gen = None
        self.resolved_val = None
        self.last_resolved_module_name = last_resolved_module_name
        self.last_resolved_test_id = last_resolved_test_id

    @property
    def key(self) -> str:
        path = inspect.getfile(fixture)
        name = self.name
        return f"{path}::{name}"

    @property
    def scope(self) -> Scope:
        return getattr(self.fn, "ward_meta").scope

    @property
    def name(self):
        return self.fn.__name__

    @property
    def is_generator_fixture(self):
        return inspect.isgeneratorfunction(inspect.unwrap(self.fn))

    def deps(self):
        return inspect.signature(self.fn).parameters

    def teardown(self):
        # Suppress because we can't know whether there's more code
        # to execute below the yield.
        with suppress(StopIteration, RuntimeError):
            if self.is_generator_fixture:
                next(self.gen)


@dataclass
class FixtureCache:
    _fixtures: Dict[str, Fixture] = field(default_factory=dict)

    def cache_fixture(self, fixture: Fixture):
        self._fixtures[fixture.key] = fixture

    def teardown_all(self):
        """Run the teardown code for all generator fixtures in the cache"""
        vals = [f for f in self._fixtures.values()]
        for fixture in vals:
            with suppress(RuntimeError, StopIteration):
                fixture.teardown()
                del self[fixture.key]

    def get(
        self, scope: Optional[Scope], module_name: Optional[str], test_id: Optional[str]
    ) -> List[Fixture]:
        filtered_by_mod = [
            f
            for f in self._fixtures.values()
            if f.scope == scope and f.last_resolved_module_name == module_name
        ]

        if test_id:
            return [f for f in filtered_by_mod if f.last_resolved_test_id == test_id]
        else:
            return filtered_by_mod

    def teardown_fixtures(self, fixtures: List[Fixture]):
        for fixture in fixtures:
            if fixture.key in self:
                with suppress(RuntimeError, StopIteration):
                    fixture.teardown()
                    del self[fixture.key]

    def __contains__(self, key: str) -> bool:
        return key in self._fixtures

    def __getitem__(self, key: str) -> Fixture:
        return self._fixtures[key]

    def __delitem__(self, key: str):
        del self._fixtures[key]

    def __len__(self):
        return len(self._fixtures)


def fixture(func=None, *, scope: Optional[Union[Scope, str]] = Scope.Test):
    if not isinstance(scope, Scope):
        scope = Scope.from_str(scope)

    if func is None:
        return partial(fixture, scope=scope)

    # By setting is_fixture = True, the framework will know
    # that if this fixture is provided as a default arg, it
    # is responsible for resolving the value.
    if hasattr(func, "ward_meta"):
        func.ward_meta.is_fixture = True
    else:
        func.ward_meta = WardMeta(is_fixture=True, scope=scope)

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
