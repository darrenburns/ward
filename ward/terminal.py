import os
import sys
import traceback
from dataclasses import dataclass
from enum import Enum
from typing import Generator, List, Optional, Tuple

from colorama import Fore, Style
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

    def __init__(self, suite: Suite):
        self.suite = suite
        self.terminal_size = get_terminal_size()

    def output_all_test_results(
        self,
        test_results_gen: Generator[TestResult, None, None],
        time_to_collect: float,
        fail_limit: Optional[int] = None,
    ) -> List[TestResult]:
        all_results = []
        failed_test_results = []
        print(f"Ward collected {self.suite.num_tests} tests and {self.suite.num_fixtures} fixtures "
              f"in {time_to_collect:.2f} seconds.\n")
        for result in test_results_gen:
            self.output_single_test_result(result)
            sys.stdout.write(Style.RESET_ALL)
            all_results.append(result)
            if result.outcome == TestOutcome.FAIL:
                failed_test_results.append(result)

            if len(failed_test_results) == fail_limit:
                break

        print()
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


def lightblack(s: str) -> str:
    return f"{Fore.LIGHTBLACK_EX}{s}{Style.RESET_ALL}"


@dataclass
class TerminalSize:
    height: int
    width: int


def get_terminal_size() -> TerminalSize:
    for i in range(0, 3):
        try:
            cols, rows = os.get_terminal_size(i)
            return TerminalSize(height=rows, width=cols)
        except OSError:
            continue
    return TerminalSize(height=24, width=80)


class SimpleTestResultWrite(TestResultWriterBase):

    def output_single_test_result(self, test_result: TestResult):
        outcome_to_colour = {
            TestOutcome.PASS: "green",
            TestOutcome.SKIP: "blue",
            TestOutcome.FAIL: "red",
        }
        colour = outcome_to_colour[test_result.outcome]
        bg = f"on_{colour}"
        padded_outcome = f" {test_result.outcome.name} "
        mod_name = lightblack(f"{test_result.test.module.__name__}.")
        print(colored(padded_outcome, color='grey', on_color=bg),
              mod_name,
              test_result.test.name)

    def output_why_test_failed_header(self, test_result: TestResult):
        print(colored(" Failure", color="red", attrs=["bold"]), "in",
              colored(test_result.test.qualified_name, attrs=["bold"]))

    def output_why_test_failed(self, test_result: TestResult):
        truncation_chars = self.terminal_size.width - 16
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
                    f"\n  Showing diff of {colored('expected value', color='green')}"
                    f" vs {colored('actual value', color='red')}:\n")

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
        print(self.generate_chart(num_passed=num_passed, num_failed=num_failed, num_skipped=num_skipped), "")

        if any(r.outcome == TestOutcome.FAIL for r in test_results):
            result = colored("FAILED", color='red', attrs=["bold"])
        else:
            result = colored("PASSED", color='green', attrs=["bold"])
        print(f"{result} in {time_taken:.2f} seconds [ "
              f"{colored(str(num_failed) + ' failed', color='red')}  "
              f"{colored(str(num_skipped) + ' skipped', color='blue')}  "
              f"{colored(str(num_passed) + ' passed', color='green')} ]")

    def generate_chart(self, num_passed, num_failed, num_skipped):
        pass_pct = num_passed / max(num_passed + num_failed + num_skipped, 1)
        fail_pct = num_failed / max(num_passed + num_failed + num_skipped, 1)
        skip_pct = 1.0 - pass_pct - fail_pct

        num_green_bars = int(pass_pct * self.terminal_size.width)
        num_red_bars = int(fail_pct * self.terminal_size.width)
        num_blue_bars = int(skip_pct * self.terminal_size.width)

        # Rounding to integers could leave us a few bars short
        num_bars_remaining = self.terminal_size.width - num_green_bars - num_red_bars - num_blue_bars
        if num_bars_remaining and num_green_bars:
            num_green_bars += 1
            num_bars_remaining -= 1

        if num_bars_remaining and num_red_bars:
            num_red_bars += 1
            num_bars_remaining -= 1

        if num_bars_remaining and num_blue_bars:
            num_blue_bars += 1
            num_bars_remaining -= 1

        assert num_bars_remaining == 0

        if self.terminal_size.width - num_green_bars - num_red_bars == 1:
            num_green_bars += 1

        return (colored("F" * num_red_bars, color="red", on_color="on_red") +
                colored("s" * num_blue_bars, color="blue", on_color="on_blue") +
                colored("." * num_green_bars, color="green", on_color="on_green"))

    def output_test_run_post_failure_summary(self, test_results: List[TestResult]):
        pass

    def _get_num_passed_failed_skipped(self, test_results: List[TestResult]) -> Tuple[int, int, int]:
        num_passed = len([r for r in test_results if r.outcome == TestOutcome.PASS])
        num_failed = len([r for r in test_results if r.outcome == TestOutcome.FAIL])
        num_skipped = len([r for r in test_results if r.outcome == TestOutcome.SKIP])

        return num_passed, num_failed, num_skipped
