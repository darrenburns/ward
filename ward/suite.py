import io
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from typing import Generator, List

from ward.errors import FixtureError
from ward.fixtures import FixtureCache, Fixture
from ward.models import Scope
from ward.testing import Test, TestOutcome, TestResult


@dataclass
class Suite:
    tests: List[Test]
    cache: FixtureCache = field(default_factory=FixtureCache)

    @property
    def num_tests(self):
        return len(self.tests)

    def generate_test_runs(self) -> Generator[TestResult, None, None]:
        previous_test_module = None
        for test in self.tests:
            if previous_test_module and test.module_name != previous_test_module:
                # We've moved into a different module, so clear out all of
                # the module scoped fixtures from the previous module.
                to_teardown = self.cache.get(
                    scope=Scope.Module, module_name=previous_test_module, test_id=None
                )
                self.cache.teardown_fixtures(to_teardown)

            generated_tests = test.get_parameterised_instances()
            for i, generated_test in enumerate(generated_tests):
                marker = generated_test.marker.name if generated_test.marker else None
                if marker == "SKIP":
                    yield generated_test.get_result(TestOutcome.SKIP)
                    previous_test_module = generated_test.module_name
                    continue

                try:
                    resolved_vals = generated_test.resolve_args(self.cache, iteration=i)

                    # Run the test, while capturing output.
                    generated_test(**resolved_vals)

                    # The test has completed without exception and therefore passed
                    outcome = (
                        TestOutcome.XPASS if marker == "XFAIL" else TestOutcome.PASS
                    )
                    yield generated_test.get_result(outcome)

                except FixtureError as e:
                    # We can't run teardown code here because we can't know how much
                    # of the fixture has been executed.
                    yield generated_test.get_result(TestOutcome.FAIL, e)
                    previous_test_module = generated_test.module_name
                    continue

                except Exception as e:
                    # TODO: Differentiate between ExpectationFailed and other Exceptions.
                    outcome = (
                        TestOutcome.XFAIL if marker == "XFAIL" else TestOutcome.FAIL
                    )
                    yield generated_test.get_result(outcome, e)

                self._teardown_fixtures_scoped_to_test(generated_test)
                previous_test_module = generated_test.module_name

        # Take care of any additional teardown.
        self.cache.teardown_all()

    def _teardown_fixtures_scoped_to_test(self, test: Test):
        """
        Get all the test-scoped fixtures that were used to form this result,
        tear them down from the cache, and return the result.
        """
        to_teardown = self.cache.get(
            scope=Scope.Test, test_id=test.id, module_name=test.module_name
        )
        self.cache.teardown_fixtures(to_teardown)
