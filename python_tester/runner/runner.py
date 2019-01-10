import inspect
import logging
from typing import Generator, Callable

from python_tester.collect.fixtures import FixtureError, FixtureRegistry
from python_tester.models.test_result import TestResult


def run_tests(
        tests: Generator[Callable, None, None],
        fixture_registry: FixtureRegistry
) -> Generator[TestResult, None, None]:
    for test_fn in tests:
        test_name = test_fn.__name__
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
