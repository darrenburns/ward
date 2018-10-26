import inspect
from typing import Callable, Mapping


class FixtureError(Exception):
    pass


class FixtureRegistry:
    def __init__(self):
        self._fixtures = {}

        def wrapper(func):
            self._fixtures[func.__name__] = func
            return func

        self._wrapper = wrapper

    @property
    def decorator(self):
        return self._wrapper

    def get_fixtures_for_test(self, test_func: Callable) -> Mapping[str, Callable]:
        fixture_names = inspect.signature(test_func).parameters
        return {name: self._get_fixture(name) for name in fixture_names}

    def _get_fixture(self, fixture_name: str) -> Callable:
        try:
            return self._fixtures[fixture_name]
        except KeyError:
            raise FixtureError(f"Couldn't find fixture '{fixture_name}'")

    def get_all(self):
        return self._fixtures


fixture_registry = FixtureRegistry()
fixture = fixture_registry.decorator
