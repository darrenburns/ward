import inspect
import logging
from typing import Any, Generator, Iterable

from python_tester.collect.fixtures import FixtureError, FixtureRegistry
from python_tester.models.test_result import TestResult


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
                        yield TestResult(test_name, False, e, message="Error! " + str(e))
                        continue

                    try:
                        test_fn(**args)
                        yield TestResult(test_name, True, None)
                    except Exception as e:
                        logging.exception("Test failed")
                        yield TestResult(test_name, False, e)
