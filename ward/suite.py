import inspect
import io
from contextlib import redirect_stderr, redirect_stdout, suppress
from dataclasses import dataclass
from typing import Generator, List

from ward.fixtures import FixtureExecutionError, FixtureCache
from ward.test_result import TestOutcome, TestResult
from ward.testing import Test


@dataclass
class Suite:
    tests: List[Test]
    fixture_cache: FixtureCache

    @property
    def num_tests(self):
        return len(self.tests)

    @property
    def num_fixtures(self):
        return len(self.fixture_cache)

    def generate_test_runs(self) -> Generator[TestResult, None, None]:
        for test in self.tests:
            marker = test.marker.name if test.marker else None
            if marker == "SKIP":
                yield TestResult(test, TestOutcome.SKIP)
                continue

            sout, serr = io.StringIO(), io.StringIO()
            try:
                with redirect_stdout(sout), redirect_stderr(serr):
                    resolved_fixtures = test.resolve_fixtures()
            except FixtureExecutionError as e:
                yield TestResult(
                    test,
                    TestOutcome.FAIL,
                    e,
                    captured_stdout=sout.getvalue(),
                    captured_stderr=serr.getvalue(),
                )
                sout.close()
                serr.close()
                continue
            try:
                resolved_vals = {
                    k: fix.resolved_val for (k, fix) in resolved_fixtures.arguments.items()
                }

                # Run the test, while capturing output.
                with redirect_stdout(sout), redirect_stderr(serr):
                    test(**resolved_vals)

                # The test has completed without exception and therefore passed
                if marker == "XFAIL":
                    yield TestResult(
                        test,
                        TestOutcome.XPASS,
                        captured_stdout=sout.getvalue(),
                        captured_stderr=serr.getvalue(),
                    )
                else:
                    yield TestResult(test, TestOutcome.PASS)

            except Exception as e:
                if marker == "XFAIL":
                    yield TestResult(test, TestOutcome.XFAIL, e)
                else:
                    yield TestResult(
                        test,
                        TestOutcome.FAIL,
                        e,
                        captured_stdout=sout.getvalue(),
                        captured_stderr=serr.getvalue(),
                    )
            finally:
                # TODO: Don't just cleanup top-level dependencies, since there may
                #  be generator fixtures elsewhere in the tree requiring cleanup
                print("resolved_fixtures", resolved_fixtures)
                for fixture in resolved_fixtures.arguments.values():
                    if inspect.isgeneratorfunction(fixture):
                        with suppress(RuntimeError, StopIteration):
                            fixture.cleanup()

                sout.close()
                serr.close()
