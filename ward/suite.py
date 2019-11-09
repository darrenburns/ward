from collections import defaultdict
from dataclasses import dataclass, field
from typing import Generator, List

from ward import Scope
from ward.errors import FixtureError
from ward.fixtures import FixtureCache
from ward.testing import Test, TestOutcome, TestResult


@dataclass
class Suite:
    tests: List[Test]
    cache: FixtureCache = field(default_factory=FixtureCache)

    @property
    def num_tests(self):
        return len(self.tests)

    def _test_counts_per_module(self):
        module_paths = [test.path for test in self.tests]
        counts = defaultdict(int)
        for path in module_paths:
            counts[path] += 1
        return counts

    def generate_test_runs(self) -> Generator[TestResult, None, None]:
        num_tests_per_module = self._test_counts_per_module()
        for test in self.tests:
            generated_tests = test.get_parameterised_instances()
            for i, generated_test in enumerate(generated_tests):
                marker = generated_test.marker.name if generated_test.marker else None
                if marker == "SKIP":
                    yield generated_test.get_result(TestOutcome.SKIP)
                    continue

                try:
                    resolved_vals = generated_test.resolve_args(self.cache, iteration=i)
                    generated_test(**resolved_vals)
                    outcome = (
                        TestOutcome.XPASS if marker == "XFAIL" else TestOutcome.PASS
                    )
                    yield generated_test.get_result(outcome)
                except FixtureError as e:
                    yield generated_test.get_result(TestOutcome.FAIL, e)
                    continue
                except Exception as e:
                    outcome = (
                        TestOutcome.XFAIL if marker == "XFAIL" else TestOutcome.FAIL
                    )
                    yield generated_test.get_result(outcome, e)
                finally:
                    num_tests_per_module[generated_test.path] -= 1

                self.cache.teardown_fixtures_for_scope(Scope.Test, generated_test.id)

                # TODO: Check if we've finished running all tests in the
                #  current module, and if so, teardown fixtures for that scope
                #  using the module path as the scope key.

        self.cache.teardown_global_fixtures()
