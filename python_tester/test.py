import inspect
from types import MappingProxyType
from typing import Any, Callable, Dict, Tuple

from python_tester.fixtures import FixtureRegistry


class Test:
    def __init__(self, test_function: Callable, module: Any):
        self.test_function = test_function
        self.module = module

        self.name = test_function.__name__

    def __call__(self, *args, **kwargs):
        return self.test_function(*args, **kwargs)

    def fn(self) -> Callable:
        return self.test_function

    def deps(self) -> MappingProxyType:
        return inspect.signature(self.fn()).parameters

    def has_deps(self) -> bool:
        return len(self.deps()) > 0

    def resolve_args(self, fixture_registry: FixtureRegistry) -> Dict[str, Any]:
        """Resolve fixture that has been injected into this test"""
        if not self.has_deps():
            return {}

        # Construct a dict of kwargs to pass into the test when it's called
        resolved_args = {}
        for fixture_name in self.deps():
            fixture = fixture_registry[fixture_name]
            resolved_arg = fixture.resolve(fixture_registry)
            resolved_args[fixture_name] = resolved_arg

        return resolved_args
