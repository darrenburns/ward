from dataclasses import dataclass
from typing import Generator, List

from python_tester.fixtures import FixtureExecutionError, FixtureRegistry
from python_tester.test import Test
from python_tester.test_result import TestResult


@dataclass
class Suite:
    tests: List[Test]
    fixture_registry: FixtureRegistry

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
                yield TestResult(test, True, None, message="")
            except Exception as e:
                yield TestResult(test, False, e, message="")
