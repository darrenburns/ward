import inspect
from typing import Callable, Dict, Mapping

from python_tester.models.test import Test


class FixtureError(Exception):
    pass


class FixtureRegistry:
    def __init__(self):
        self._fixtures = {}

        def wrapper(func):
            if func.__name__ not in self._fixtures:
                self._fixtures[func.__name__] = func
            else:
                raise FixtureError(f"Multiple fixtures named '{func.__name__}'.")
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

    def resolve_fixtures_for_test(self, test: Test) -> Mapping[str, Callable]:
        resolved_fixtures = {}
        args = self._get_fixtures_for_func(test.test_function, resolved_fixtures, 0)
        return args

    def _get_fixtures_for_func(self, func, out_fixtures, depth) -> Dict:
        dep_names = inspect.signature(func).parameters
        fixture_name = func.__name__
        if len(dep_names) == 0:
            # We've reached a leaf node of the fixture dependency tree (base case)
            out_fixtures[fixture_name] = func()
            return {}
        else:
            # Resolve as we traverse fixture tree
            args = {}
            for dep_name in dep_names:
                is_recursive_dependency = dep_name == fixture_name
                if is_recursive_dependency:
                    raise FixtureError(f"Fixture {func} depends on itself.")

                fixture = self._get_fixture(dep_name)
                self._get_fixtures_for_func(fixture, out_fixtures, depth + 1)
                args = {dep_name: out_fixtures.get(dep_name), **args}

            # Don't execute the root of the fixture tree (the test itself)
            if depth == 0:
                return args

            out_fixtures[fixture_name] = func(**args)

            return args


fixture_registry = FixtureRegistry()
fixture = fixture_registry.decorator
