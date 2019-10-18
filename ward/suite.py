from dataclasses import dataclass
from typing import Generator, List

from ward.fixtures import FixtureExecutionError, FixtureRegistry
from ward.test import Test, WardMarker
from ward.test_result import TestResult, TestOutcome


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
            if test.marker == WardMarker.SKIP:
                yield TestResult(test, TestOutcome.SKIP, None, "")
                continue

            try:
                resolved_fixtures = test.resolve_args(self.fixture_registry)
            except FixtureExecutionError as e:
                yield TestResult(test, TestOutcome.FAIL, e)
                continue
            try:
                resolved_vals = {k: fix.resolved_val for (k, fix) in resolved_fixtures.items()}

                # Run the test
                test(**resolved_vals)

                # The test has completed without exception and therefore passed
                if test.marker == WardMarker.XFAIL:
                    yield TestResult(test, TestOutcome.XPASS, None)
                else:
                    yield TestResult(test, TestOutcome.PASS, None)

            except Exception as e:
                if test.marker == WardMarker.XFAIL:
                    yield TestResult(test, TestOutcome.XFAIL, e)
                else:
                    yield TestResult(test, TestOutcome.FAIL, e)
            finally:
                for fixture in resolved_fixtures.values():
                    if fixture.is_generator_fixture:
                        try:
                            fixture.cleanup()
                        except (RuntimeError, StopIteration):
                            # In Python 3.7, a RuntimeError is raised if we fall off the end of a generator
                            # (instead of a StopIteration)
                            pass
