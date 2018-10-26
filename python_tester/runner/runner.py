import inspect
from typing import Any, Callable, Generator, Iterable, Mapping

from python_tester.collect.fixtures import FixtureError, FixtureRegistry
from python_tester.models.test_result import TestResult


# def resolve_fixtures(fixture_map: Mapping[str, Callable]) -> Mapping[str, Any]:
    # Check if the fixture takes any args (other fixtures itself)
    # return {name: func() for name, func in fixture_map.items()}


def run_tests_in_modules(
    modules: Iterable[Any], fixture_registry: FixtureRegistry
) -> Generator[TestResult, None, None]:
    for mod in modules:
        for item in dir(mod):
            if item.startswith("test_"):
                test_name = item
                test_fn = getattr(mod, test_name)
                if inspect.isfunction(test_fn):
                    try:
                        args = fixture_registry.resolve_fixtures_for_test(test_fn)
                    except FixtureError as e:
                        yield TestResult(test_name, False, e, message=str(e))
                        continue

                    try:
                        test_fn(**args)
                        yield TestResult(test_name, True, None)
                    except Exception as e:
                        yield TestResult(test_name, False, e)
