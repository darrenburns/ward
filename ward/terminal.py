import sys
import traceback
from enum import Enum
from typing import Generator, List, Optional, Tuple

from blessings import Terminal
from colorama import Back, Fore, Style
from termcolor import colored

from ward.diff import build_auto_diff
from ward.expect import ExpectationFailed
from ward.suite import Suite
from ward.test_result import TestOutcome, TestResult


def truncate(s: str, num_chars: int) -> str:
    suffix = "..." if len(s) > num_chars - 3 else ""
    return s[:num_chars] + suffix


class ExitCode(Enum):
    SUCCESS = 0
    TEST_FAILED = 1
    ERROR = 2


class TestResultWriterBase:

    def __init__(self, terminal: Terminal, suite: Suite):
        self.terminal = terminal
        self.suite = suite

    def output_all_test_results(
        self,
        test_results_gen: Generator[TestResult, None, None],
        time_to_collect: float,
        fail_limit: Optional[int] = None,
    ) -> List[TestResult]:
        all_results = []
        failed_test_results = []
        print(f"Ward collected {self.suite.num_tests} tests and {self.suite.num_fixtures} fixtures "
              f"in {time_to_collect:.2f} seconds.{Style.RESET_ALL}")
        for result in test_results_gen:
            self.output_single_test_result(result)
            sys.stdout.write(Style.RESET_ALL)
            all_results.append(result)
            if result.outcome == TestOutcome.FAIL:
                failed_test_results.append(result)

            if len(failed_test_results) == fail_limit:
                break

        self.output_test_run_post_failure_summary(test_results=all_results)
        for failure in failed_test_results:
            self.output_why_test_failed_header(failure)
            self.output_why_test_failed(failure)

        return all_results

    def output_single_test_result(self, test_result: TestResult):
        """Indicate whether a test passed, failed, was skipped etc."""
        raise NotImplementedError()

    def output_why_test_failed_header(self, test_result: TestResult):
        """
        Printed above the failing test output
        """
        raise NotImplementedError()

    def output_test_result_summary(self, test_results: List[TestResult], time_taken: float):
        raise NotImplementedError()

    def output_why_test_failed(self, test_result: TestResult):
        """
        Extended output shown for failing tests, may include further explanations,
        assertion error info, diffs, etc.
        """
        raise NotImplementedError()

    def output_test_run_post_failure_summary(self, test_results: List[TestResult]):
        raise NotImplementedError()


class SimpleTestResultWrite(TestResultWriterBase):

    def output_single_test_result(self, test_result: TestResult):
        outcome_to_bg = {
            TestOutcome.PASS: Back.GREEN,
            TestOutcome.SKIP: Back.YELLOW,
            TestOutcome.FAIL: Back.RED,
        }
        bg = outcome_to_bg[test_result.outcome]
        print(f"{bg}{Fore.BLACK} {test_result.outcome.name} {Style.RESET_ALL} "
              f"{Fore.LIGHTBLACK_EX}{test_result.test.module.__name__}.{Style.RESET_ALL}{test_result.test.name}")

    def output_why_test_failed_header(self, test_result: TestResult):
        test_name = test_result.test.name
        test_module = test_result.test.module.__name__
        test_result_heading = f"{Fore.BLACK}{Back.RED} FAIL | {test_module}.{test_name} {Style.RESET_ALL}"
        print(f"{test_result_heading}")

    def output_why_test_failed(self, test_result: TestResult):
        truncation_chars = self.terminal.width - 30
        err = test_result.error
        if isinstance(err, ExpectationFailed):
            print(f"\n  Given {truncate(repr(err.history[0].this), num_chars=truncation_chars)}")

            for expect in err.history:
                if expect.success:
                    result_marker = f"[ {Fore.GREEN}✓{Style.RESET_ALL} ]{Fore.GREEN}"
                else:
                    result_marker = f"[ {Fore.RED}✗{Style.RESET_ALL} ]{Fore.RED}"

                if expect.op == "satisfies" and hasattr(expect.that, "__name__"):
                    expect_that = truncate(expect.that.__name__, num_chars=truncation_chars)
                else:
                    expect_that = truncate(repr(expect.that), num_chars=truncation_chars)
                print(
                    f"    {result_marker} it {expect.op} {expect_that}{Style.RESET_ALL}",
                )

            if err.history and err.history[-1].op == "equals":
                expect = err.history[-1]
                print(
                    f"\n  Showing diff of {Fore.GREEN}expected value"
                    f"{Fore.RESET} vs {Fore.RED}actual value{Fore.RESET}:\n")

                diff = build_auto_diff(expect.that, expect.this, width=truncation_chars)
                print(diff)
        else:
            trace = getattr(err, "__traceback__", "")
            if trace:
                trc = traceback.format_exception(None, err, trace)
                print("".join(trc))
            else:
                print(str(err))

        print(Style.RESET_ALL)

    def output_test_result_summary(self, test_results: List[TestResult], time_taken: float):
        num_passed, num_failed, num_skipped = self._get_num_passed_failed_skipped(test_results)
        if self.terminal.is_a_tty:
            print(self.generate_chart(num_passed=num_passed, num_failed=num_failed, num_skipped=num_skipped))

        if any(r.outcome == TestOutcome.FAIL for r in test_results):
            result = colored("FAILED", color='red')
        else:
            result = colored("PASSED", color='green')
        print(f"{result} in {time_taken:.2f} seconds [ "
              f"{colored(str(num_failed) + ' failed', color='red')}  "
              f"{colored(str(num_skipped) + ' skipped', color='cyan')}  "
              f"{colored(str(num_passed) + ' passed', color='green')} ]")

    def generate_chart(self, num_passed, num_failed, num_skipped):
        pass_pct = num_passed / max(num_passed + num_failed + num_skipped, 1)
        fail_pct = num_failed / max(num_passed + num_failed + num_skipped, 1)
        skip_pct = 1.0 - pass_pct - fail_pct

        num_green_bars = int(pass_pct * self.terminal.width)
        num_red_bars = int(fail_pct * self.terminal.width)
        num_yellow_bars = int(skip_pct * self.terminal.width)

        # Rounding to integers could leave us a few bars short
        num_bars_remaining = self.terminal.width - num_green_bars - num_red_bars - num_yellow_bars
        if num_bars_remaining and num_green_bars:
            num_green_bars += 1
            num_bars_remaining -= 1

        if num_bars_remaining and num_red_bars:
            num_red_bars += 1
            num_bars_remaining -= 1

        if num_bars_remaining and num_yellow_bars:
            num_yellow_bars += 1
            num_bars_remaining -= 1

        assert num_bars_remaining == 0

        if self.terminal.width - num_green_bars - num_red_bars == 1:
            num_green_bars += 1

        return (self.terminal.red("█" * num_red_bars) +
                self.terminal.yellow("█" * num_yellow_bars) +
                self.terminal.green("█" * num_green_bars))

    def output_test_run_post_failure_summary(self, test_results: List[TestResult]):
        num_passed, num_failed, num_skipped = self._get_num_passed_failed_skipped(test_results)
        if any(r.outcome == TestOutcome.FAIL for r in test_results):
            if self.terminal.is_a_tty:
                print(self.generate_chart(num_passed, num_failed, num_skipped))

    def _get_num_passed_failed_skipped(self, test_results: List[TestResult]) -> Tuple[int, int, int]:
        num_passed = len([r for r in test_results if r.outcome == TestOutcome.PASS])
        num_failed = len([r for r in test_results if r.outcome == TestOutcome.FAIL])
        num_skipped = len([r for r in test_results if r.outcome == TestOutcome.SKIP])

        return num_passed, num_failed, num_skipped
