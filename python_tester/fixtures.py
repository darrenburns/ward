import inspect
from typing import Any, Callable, Dict, Iterable


class TestSetupError(Exception):
    pass


class CollectionError(TestSetupError):
    pass


class FixtureExecutionError(Exception):
    pass


class Fixture:
    def __init__(self, key: str, fn: Callable):
        self.key = key
        self.fn = fn
        self.resolved_val = None
        self.is_resolved = False

    def fn(self):
        return self.fn

    def deps(self):
        return inspect.signature(self.fn).parameters

    def resolve(self, fix_registry) -> Any:
        """Traverse the fixture tree to resolve the value of this fixture"""

        # If this fixture has no children, cache and return the resolved value
        if not self.deps():
            try:
                self.resolved_val = self.fn()
            except Exception as e:
                raise FixtureExecutionError(f"Unable to execute fixture '{self.key}'") from e
            fix_registry.cache_fixture(self)
            return self.resolved_val

        # Otherwise, we have to find the child fixture vals, and call self
        children = self.deps()
        children_resolved = []
        for child in children:
            child_fixture = fix_registry[child]
            child_resolved_val = child_fixture.resolve(fix_registry)
            children_resolved.append(child_resolved_val)

        # We've resolved the values of all child fixtures
        try:
            self.resolved_val = self.fn(*children_resolved)
        except Exception as e:
            raise FixtureExecutionError(f"Unable to execute fixture '{self.key}'") from e

        fix_registry.cache_fixture(self)
        return self.resolved_val


class FixtureRegistry:
    def __init__(self):
        self._fixtures: Dict[str, Fixture] = {}

        def wrapper(func):
            name = func.__name__
            if name not in self._fixtures:
                self._fixtures[name] = Fixture(key=name, fn=func)
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
            raise CollectionError(f"Couldn't find fixture '{fixture_name}'.")

    def cache_fixture(self, fixture: Fixture):
        """Update the fixture in the registry, for example, replace it with its resolved analogue"""
        # TODO: Caching can be used to implement fixture scoping,
        #  but currently resolved cached fixtures aren't used.
        self._fixtures[fixture.key] = fixture

    def cache_fixtures(self, fixtures: Iterable[Fixture]):
        for fixture in fixtures:
            self.cache_fixture(fixture)

    def __getitem__(self, item):
        return self._fixtures[item]

    def __len__(self):
        return len(self._fixtures)


fixture_registry = FixtureRegistry()
fixture = fixture_registry.decorator
