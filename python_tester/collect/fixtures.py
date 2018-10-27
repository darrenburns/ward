import inspect
from typing import Callable, Dict, Mapping


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

    def _get_fixture(self, fixture_name: str) -> Callable:
        try:
            return self._fixtures[fixture_name]
        except KeyError:
            raise FixtureError(f"Couldn't find fixture '{fixture_name}'")

    def get_all(self):
        return self._fixtures

    def resolve_fixtures_for_test(self, test_func: Callable) -> Mapping[str, Callable]:
        resolved_fixtures = {}
        args = self._get_fixtures_for_func(test_func, resolved_fixtures, 0)
        return args

    def _get_fixtures_for_func(self, func, out_fixtures, depth) -> Dict:
        dep_names = inspect.signature(func).parameters
        if len(dep_names) == 0:
            # We've a leaf node of the fixture dependency tree (base case)
            resolved = func()
            out_fixtures[func.__name__] = resolved
            return {}
        else:
            # Resolve as we traverse fixture tree
            args = {}
            for dep_name in dep_names:
                fixture = self._get_fixture(dep_name)
                self._get_fixtures_for_func(fixture, out_fixtures, depth + 1)
                args = {dep_name: out_fixtures.get(dep_name), **args}

            if depth == 0:
                return args

            resolved = func(**args)
            out_fixtures[func.__name__] = resolved


fixture_registry = FixtureRegistry()
fixture = fixture_registry.decorator
