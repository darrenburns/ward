import inspect
from typing import Callable, Dict, Iterable


class TestSetupError(Exception):
    pass


class CollectionError(TestSetupError):
    pass


class FixtureExecutionError(Exception):
    pass


class Fixture:
    def __init__(self, key: str, fn: Callable, is_generator_fixture: bool = False):
        self.key = key
        self.fn = fn
        self.is_generator_fixture = is_generator_fixture
        self.gen = None
        self.resolved_val = None
        self.is_resolved = False

    def deps(self):
        return inspect.signature(self.fn).parameters

    def resolve(self, fix_registry) -> "Fixture":
        """Traverse the fixture tree to resolve the value of this fixture"""

        # If this fixture has no children, cache and return the resolved value
        if not self.deps():
            try:
                if inspect.isgeneratorfunction(self.fn):
                    self.gen = self.fn()
                    self.resolved_val = next(self.gen)
                else:
                    self.resolved_val = self.fn()
            except Exception as e:
                raise FixtureExecutionError(
                    f"Unable to execute fixture '{self.key}'"
                ) from e
            fix_registry.cache_fixture(self)
            return self

        # Otherwise, we have to find the child fixture vals, and call self
        children = self.deps()
        children_resolved = []
        for child in children:
            child_fixture = fix_registry[child].resolve(fix_registry)
            children_resolved.append(child_fixture)

        # We've resolved the values of all child fixtures
        try:
            child_resolved_vals = [child.resolved_val for child in children_resolved]
            if inspect.isgeneratorfunction(self.fn):
                self.gen = self.fn(*child_resolved_vals)
                self.resolved_val = next(self.gen)
            else:
                self.resolved_val = self.fn(*child_resolved_vals)
        except Exception as e:
            raise FixtureExecutionError(
                f"Unable to execute fixture '{self.key}'"
            ) from e

        fix_registry.cache_fixture(self)
        return self

    def cleanup(self):
        if self.is_generator_fixture:
            next(self.gen)


class FixtureRegistry:
    def __init__(self):
        self._fixtures: Dict[str, Fixture] = {}

    @property
    def decorator(self):
        def wrapper(func):
            name = func.__name__
            if name not in self._fixtures:
                self._fixtures[name] = Fixture(
                    key=name,
                    fn=func,
                    is_generator_fixture=inspect.isgeneratorfunction(func),
                )
            else:
                raise CollectionError(f"Multiple fixtures named '{func.__name__}'.")
            return func

        return wrapper

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
