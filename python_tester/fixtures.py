import inspect
from typing import Dict, Union, Callable, Any

from python_tester.test import Test


class TestSetupError(Exception):
    pass


class CollectionError(TestSetupError):
    pass


class FixtureExecutionError(Exception):
    pass


class Fixture:
    def __init__(self, name: str, fn: Callable):
        self.name = name
        self.fn = fn
        self.resolved_val = None
        self.is_resolved = False

    def fn(self):
        return self.fn

    def resolve(self, *args, **kwargs) -> Any:
        try:
            self.resolved_val = self.fn(*args, **kwargs)
        except Exception as e:
            raise FixtureExecutionError(f"Error occurred in fixture '{self.name}'.") from e
        self.is_resolved = True
        return self.resolved_val


class FixtureRegistry:
    def __init__(self):
        self._fixtures: Dict[str, Fixture] = {}

        def wrapper(func):
            name = func.__name__
            if name not in self._fixtures:
                self._fixtures[name] = Fixture(name=name, fn=func)
            else:
                raise CollectionError(f"Multiple fixtures named '{func.__name__}'.")
            return func

        self._wrapper = wrapper

    @property
    def decorator(self):
        return self._wrapper

    def _get_fixture(self, fixture_name: str) -> Fixture:
        try:
            return self._fixtures[fixture_name]
        except KeyError:
            raise CollectionError(f"Couldn't find fixture '{fixture_name}'")

    def get_all(self):
        return self._fixtures

    def resolve_fixtures_for_test(self, test: Test) -> Dict[str, Fixture]:
        if not test.has_deps():
            return {}

        resolved_fixtures: Dict[str, Fixture] = {}
        args = self._resolve_deps(test, resolved_fixtures, 0)
        return args

    def _resolve_deps(self, unit: Union[Test, Fixture], out_fixtures, depth) -> Dict:
        dep_names = inspect.signature(unit.fn).parameters
        breakpoint()
        fixture_name = unit.name
        if len(dep_names) == 0:
            # We've reached a leaf node of the fixture dependency tree (base case)
            out_fixtures[fixture_name] = unit()
            return {}
        else:
            # Resolve as we traverse fixture tree
            args = {}
            for dep_name in dep_names:
                is_circular_dependency = dep_name == fixture_name
                if is_circular_dependency:
                    raise CollectionError(f"Fixture {unit} depends on itself.")

                fixture = self._get_fixture(dep_name)
                self._resolve_deps(fixture, out_fixtures, depth + 1)
                args = {dep_name: out_fixtures.get(dep_name), **args}

            # Don't execute the root of the tree (the test itself)
            if depth == 0:
                return args

            out_fixtures[fixture_name] = unit(**args)

            return args

    def __len__(self):
        return len(self._fixtures)


fixture_registry = FixtureRegistry()
fixture = fixture_registry.decorator
