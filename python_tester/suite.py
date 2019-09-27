from typing import Generator, List

from python_tester.fixtures import CollectionError, FixtureRegistry, FixtureExecutionError
from python_tester.test import Test
from python_tester.test_result import TestResult


class Suite:
    def __init__(self, tests: List[Test], fixture_registry: FixtureRegistry):
        self.tests = tests
        self.fixture_registry = fixture_registry

    @property
    def num_tests(self):
        return len(self.tests)

    @property
    def num_fixtures(self):
        return len(self.fixture_registry)

    def generate_test_runs(self) -> Generator[TestResult, None, None]:
        for test in self.tests:
            try:
                resolved_fixtures = test.resolve_args(self.fixture_registry)
            except FixtureExecutionError as e:
                yield TestResult(test, False, e, message="[Error] " + str(e))
                continue
            try:
                test(**resolved_fixtures)
                yield TestResult(test, True, None)
            except Exception as e:
                yield TestResult(test, False, e)
