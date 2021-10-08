from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import DefaultDict, Dict, Generator, List

from ward._errors import ParameterisationError
from ward._fixtures import FixtureCache
from ward.fixtures import TeardownResult
from ward.models import Scope
from ward.testing import Test, TestResult


@dataclass
class Suite:
    tests: List[Test]
    cache: FixtureCache = field(default_factory=FixtureCache)

    @property
    def num_tests(self) -> int:
        """
        Returns: The number of tests in the suite, *before* taking parameterisation into account.
        """
        return len(self.tests)

    @property
    def num_tests_with_parameterisation(self) -> int:
        """
        Returns: The number of tests in the suite, *after* taking parameterisation into account.
        """
        return sum(test.find_number_of_instances() for test in self.tests)

    def _test_counts_per_module(self) -> Dict[Path, int]:
        """
        Returns: A dictionary mapping a module Path to the number of tests that can be found within that module.
        """
        module_paths = [test.path for test in self.tests]
        counts: DefaultDict[Path, int] = defaultdict(int)
        for path in module_paths:
            counts[path] += 1
        return counts

    def generate_test_runs(
        self,
        dry_run: bool = False,
        capture_output: bool = True,
    ) -> Generator[TestResult, None, None]:
        """
        Run tests

        Returns a generator which yields test results
        """
        num_tests_per_module = self._test_counts_per_module()
        for test in self.tests:
            num_tests_per_module[test.path] -= 1
            try:
                generated_tests = test.get_parameterised_instances()
            except ParameterisationError as e:
                yield test.fail_with_error(e)
                continue
            for generated_test in generated_tests:
                result = generated_test.run(self.cache, dry_run=dry_run)
                teardown_results: List[
                    TeardownResult
                ] = self.cache.teardown_fixtures_for_scope(
                    Scope.Test,
                    scope_key=generated_test.id,
                    capture_output=capture_output,
                )
                if teardown_results:
                    try:
                        # There could be exceptions in the teardown code of multiple fixtures
                        # injected into a single test. Take the first exception and associate
                        # that with the test.
                        first_teardown_error_result: TeardownResult = next(
                            r
                            for r in teardown_results
                            if r.captured_exception is not None
                        )
                        # Any exceptions that occur during the teardown of a test-scoped fixture
                        # are considered to be an error in any test that depends on said fixture
                        result = test.fail_with_error(
                            first_teardown_error_result.captured_exception  # type: ignore[arg-type]
                        )
                    except StopIteration:
                        # There were no exceptions while tearing down the fixtures.
                        pass
                yield result

            if num_tests_per_module[test.path] == 0:
                self.cache.teardown_fixtures_for_scope(
                    Scope.Module,
                    scope_key=test.path,
                    capture_output=capture_output,
                )

        self.cache.teardown_global_fixtures(capture_output=capture_output)
