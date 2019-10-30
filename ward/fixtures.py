import inspect
from contextlib import suppress
from dataclasses import dataclass
from functools import partial, wraps
from typing import Callable, Dict, Iterable

from ward.models import WardMeta


class TestSetupError(Exception):
    pass


class CollectionError(TestSetupError):
    pass


class FixtureExecutionError(Exception):
    pass


@dataclass
class Fixture:
    def __init__(self, fn: Callable):
        self.fn = fn
        self.gen = None
        self.resolved_val = None

    @property
    def key(self):
        path = inspect.getfile(fixture)
        name = self.name
        return f"{path}::{name}"

    @property
    def name(self):
        return self.fn.__name__

    @property
    def is_generator_fixture(self):
        return inspect.isgeneratorfunction(inspect.unwrap(self.fn))

    def deps(self):
        return inspect.signature(self.fn).parameters

    def teardown(self):
        if self.is_generator_fixture:
            next(self.gen)


class FixtureCache:
    def __init__(self):
        self._fixtures: Dict[str, Fixture] = {}

    def _get_fixture(self, fixture_name: str) -> Fixture:
        try:
            return self._fixtures[fixture_name]
        except KeyError:
            raise CollectionError(f"Couldn't find fixture '{fixture_name}'.")

    def cache_fixture(self, fixture: Fixture):
        self._fixtures[fixture.key] = fixture

    def cache_fixtures(self, fixtures: Iterable[Fixture]):
        for fixture in fixtures:
            self.cache_fixture(fixture)

    def teardown_all(self):
        """Run the teardown code for all generator fixtures in the cache"""
        for fixture in self._fixtures.values():
            with suppress(RuntimeError, StopIteration):
                fixture.teardown()

    def __contains__(self, key: str):
        return key in self._fixtures

    def __getitem__(self, item):
        return self._fixtures[item]

    def __len__(self):
        return len(self._fixtures)


def fixture(func=None, *, description=None):
    if func is None:
        return partial(fixture, description=description)

    # By setting is_fixture = True, the framework will know
    # that if this fixture is provided as a default arg, it
    # is responsible for resolving the value.
    if hasattr(func, "ward_meta"):
        func.ward_meta.is_fixture = True
    else:
        func.ward_meta = WardMeta(is_fixture=True)

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
