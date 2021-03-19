from collections import defaultdict
from dataclasses import dataclass, field
from random import shuffle
from typing import Generator, List

from ward import Scope
from ward.errors import ParameterisationError
from ward.fixtures import FixtureCache
from ward.testing import Test, TestResult


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

    def generate_test_runs(
        self, order="standard", dry_run=False
    ) -> Generator[TestResult, None, None]:
        """
        Run tests

        Returns a generator which yields test results
        """

        if order == "random":
            shuffle(self.tests)

        num_tests_per_module = self._test_counts_per_module()
        for test in self.tests:
            num_tests_per_module[test.path] -= 1
            try:
                generated_tests = test.get_parameterised_instances()
            except ParameterisationError as e:
                yield test.fail_with_error(e)
                continue
            for generated_test in generated_tests:
                yield generated_test.run(self.cache, dry_run=dry_run)
                self.cache.teardown_fixtures_for_scope(
                    Scope.Test, scope_key=generated_test.id
                )

            if num_tests_per_module[test.path] == 0:
                self.cache.teardown_fixtures_for_scope(
                    Scope.Module, scope_key=test.path
                )

        self.cache.teardown_global_fixtures()
