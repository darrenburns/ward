from typing import Generator, List

from python_tester.collect.fixtures import FixtureError, FixtureRegistry
from python_tester.models.test import Test
from python_tester.models.test_result import TestResult


def run_tests(
    tests: List[Test],
    fixture_registry: FixtureRegistry
) -> Generator[TestResult, None, None]:
    for test in tests:
        try:
            args = fixture_registry.execute_fixtures_for_test(test)
        except FixtureError as e:
            yield TestResult(test, False, e, message="Error! " + str(e))
            continue
        try:
            test(**args)
            yield TestResult(test, True, None)
        except Exception as e:
            yield TestResult(test, False, e)
