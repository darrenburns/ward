import os
import sys
import traceback
from dataclasses import dataclass
from typing import Dict, Generator, List, Optional

from colorama import Fore, Style
from termcolor import colored, cprint

from ward.diff import make_diff
from ward.expect import ExpectationFailed, Expected
from ward.suite import Suite
from ward.testing import TestOutcome, TestResult
from ward.util import ExitCode, get_exit_code


def truncate(s: str, num_chars: int) -> str:
    suffix = "..." if len(s) > num_chars - 3 else ""
    return s[:num_chars] + suffix


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
        print(
            f"Ward collected {self.suite.num_tests} tests "
            f"in {time_to_collect:.2f} seconds.\n"
        )
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
            self.output_captured_stderr(failure)
            self.output_captured_stdout(failure)

        return all_results

    def output_single_test_result(self, test_result: TestResult):
        """Indicate whether a test passed, failed, was skipped etc."""
        raise NotImplementedError()

    def output_why_test_failed_header(self, test_result: TestResult):
        """
        Printed above the failing test output
        """
        raise NotImplementedError()

    def output_test_result_summary(
        self, test_results: List[TestResult], time_taken: float
    ):
        raise NotImplementedError()

    def output_why_test_failed(self, test_result: TestResult):
        """
        Extended output shown for failing tests, may include further explanations,
        assertion error info, diffs, etc.
        """
        raise NotImplementedError()

    def output_test_run_post_failure_summary(self, test_results: List[TestResult]):
        raise NotImplementedError()

    def output_captured_stderr(self, test_result: TestResult):
        raise NotImplementedError()

    def output_captured_stdout(self, test_result: TestResult):
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
            TestOutcome.XFAIL: "magenta",
            TestOutcome.XPASS: "yellow",
        }
        colour = outcome_to_colour[test_result.outcome]
        bg = f"on_{colour}"
        padded_outcome = f" {test_result.outcome.name[:4]} "
        if test_result.test.description:
            sep = f":{test_result.test.line_number}: "
        else:
            sep = "."
        mod_name = lightblack(f"{test_result.test.module_name}{sep}")
        if (
            test_result.outcome == TestOutcome.SKIP
            or test_result.outcome == TestOutcome.XFAIL
        ):
            reason = test_result.test.marker.reason or ""
            if reason:
                reason = lightblack(f" [{reason}]")
        else:
            reason = ""

        if test_result.test.description:
            name_or_desc = test_result.test.description
        else:
            name_or_desc = test_result.test.name
        print(
            colored(padded_outcome, color="grey", on_color=bg),
            mod_name + name_or_desc,
            reason,
        )

    def output_why_test_failed_header(self, test_result: TestResult):
        test = test_result.test

        if test.description:
            name_or_desc = (
                f"{test.module_name}, line {test.line_number}: {test.description}"
            )
        else:
            name_or_desc = test.qualified_name

        print(
            colored(" Failure", color="red"),
            "in",
            colored(name_or_desc, attrs=["bold"]),
            "\n",
        )

    def output_why_test_failed(self, test_result: TestResult):
        err = test_result.error
        if isinstance(err, ExpectationFailed):
            print(
                f"   Given {truncate(repr(err.history[0].this), num_chars=self.terminal_size.width - 24)}\n"
            )

            for expect in err.history:
                self.print_expect_chain_item(expect)

            last_check = err.history[-1].op  # the check that failed
            if last_check == "equals":
                self.print_failure_equals(err)
        else:
            self.print_traceback(err)

        print(Style.RESET_ALL)

    def print_failure_equals(self, err):
        expect = err.history[-1]
        print(
            f"\n   Showing diff of {colored('expected value', color='green')}"
            f" vs {colored('actual value', color='red')}:\n"
        )
        diff = make_diff(expect.that, expect.this, width=self.terminal_size.width - 24)
        print(diff)

    def print_traceback(self, err):
        trace = getattr(err, "__traceback__", "")
        if trace:
            trc = traceback.format_exception(None, err, trace)
            if err.__cause__:
                cause = err.__cause__.__class__.__name__
            else:
                cause = None
            for line in trc:
                sublines = line.split("\n")
                for subline in sublines:
                    content = " " * 4 + subline
                    if subline.lstrip().startswith('File "'):
                        cprint(content, color="yellow")
                    else:
                        print(content)
        else:
            print(str(err))

    def print_expect_chain_item(self, expect: Expected):
        checkbox = self.result_checkbox(expect)
        that_width = self.terminal_size.width - 32
        if expect.op == "satisfies" and hasattr(expect.that, "__name__"):
            expect_that = truncate(expect.that.__name__, num_chars=that_width)
        else:
            that = repr(expect.that) if expect.that else ""
            expect_that = truncate(that, num_chars=that_width)
        print(f"    {checkbox} it {expect.op} {expect_that}{Style.RESET_ALL}")

    def result_checkbox(self, expect):
        if expect.success:
            result_marker = f"[ {Fore.GREEN}✓{Style.RESET_ALL} ]{Fore.GREEN}"
        else:
            result_marker = f"[ {Fore.RED}✗{Style.RESET_ALL} ]{Fore.RED}"
        return result_marker

    def output_test_result_summary(
        self, test_results: List[TestResult], time_taken: float
    ):
        outcome_counts = self._get_outcome_counts(test_results)
        chart = self.generate_chart(
            num_passed=outcome_counts[TestOutcome.PASS],
            num_failed=outcome_counts[TestOutcome.FAIL],
            num_skipped=outcome_counts[TestOutcome.SKIP],
            num_xfail=outcome_counts[TestOutcome.XFAIL],
            num_unexp=outcome_counts[TestOutcome.XPASS],
        )
        print(chart, "")

        exit_code = get_exit_code(test_results)
        if exit_code == ExitCode.FAILED:
            result = colored(exit_code.name, color="red")
        else:
            result = colored(exit_code.name, color="green")
        print(
            f"{result} in {time_taken:.2f} seconds [ "
            f"{colored(str(outcome_counts[TestOutcome.FAIL]) + ' failed', color='red')}  "
            f"{colored(str(outcome_counts[TestOutcome.XPASS]) + ' xpassed', color='yellow')}  "
            f"{colored(str(outcome_counts[TestOutcome.XFAIL]) + ' xfailed', color='magenta')}  "
            f"{colored(str(outcome_counts[TestOutcome.SKIP]) + ' skipped', color='blue')}  "
            f"{colored(str(outcome_counts[TestOutcome.PASS]) + ' passed', color='green')} ]"
        )

    def output_captured_stderr(self, test_result: TestResult):
        if test_result.captured_stderr:
            stderr = colored("standard error", color="red")
            captured_stderr_lines = test_result.captured_stderr.split("\n")
            print(f"   Captured {stderr} during test run:\n")
            for line in captured_stderr_lines:
                print("    " + line)
            print()

    def output_captured_stdout(self, test_result: TestResult):
        if test_result.captured_stdout:
            stdout = colored("standard output", color="blue")
            captured_stdout_lines = test_result.captured_stdout.split("\n")
            print(f"   Captured {stdout} during test run:\n")
            for line in captured_stdout_lines:
                print("    " + line)

    def generate_chart(self, num_passed, num_failed, num_skipped, num_xfail, num_unexp):
        num_tests = num_passed + num_failed + num_skipped + num_xfail + num_unexp
        pass_pct = num_passed / max(num_tests, 1)
        fail_pct = num_failed / max(num_tests, 1)
        xfail_pct = num_xfail / max(num_tests, 1)
        unexp_pct = num_unexp / max(num_tests, 1)
        skip_pct = 1.0 - pass_pct - fail_pct - xfail_pct - unexp_pct

        num_green_bars = int(pass_pct * self.terminal_size.width)
        num_red_bars = int(fail_pct * self.terminal_size.width)
        num_blue_bars = int(skip_pct * self.terminal_size.width)
        num_yellow_bars = int(unexp_pct * self.terminal_size.width)
        num_magenta_bars = int(xfail_pct * self.terminal_size.width)

        # Rounding to integers could leave us a few bars short
        num_bars_remaining = (
            self.terminal_size.width
            - num_green_bars
            - num_red_bars
            - num_blue_bars
            - num_yellow_bars
            - num_magenta_bars
        )
        if num_bars_remaining and num_green_bars:
            num_green_bars += 1
            num_bars_remaining -= 1

        if num_bars_remaining and num_red_bars:
            num_red_bars += 1
            num_bars_remaining -= 1

        if num_bars_remaining and num_blue_bars:
            num_blue_bars += 1
            num_bars_remaining -= 1

        if num_bars_remaining and num_yellow_bars:
            num_yellow_bars += 1
            num_bars_remaining -= 1

        if num_bars_remaining and num_magenta_bars:
            num_magenta_bars += 1
            num_bars_remaining -= 1

        return (
            colored("F" * num_red_bars, color="red", on_color="on_red")
            + colored("U" * num_yellow_bars, color="yellow", on_color="on_yellow")
            + colored("x" * num_magenta_bars, color="magenta", on_color="on_magenta")
            + colored("s" * num_blue_bars, color="blue", on_color="on_blue")
            + colored("." * num_green_bars, color="green", on_color="on_green")
        )

    def output_test_run_post_failure_summary(self, test_results: List[TestResult]):
        pass

    def _get_outcome_counts(
        self, test_results: List[TestResult]
    ) -> Dict[TestOutcome, int]:
        return {
            TestOutcome.PASS: len(
                [r for r in test_results if r.outcome == TestOutcome.PASS]
            ),
            TestOutcome.FAIL: len(
                [r for r in test_results if r.outcome == TestOutcome.FAIL]
            ),
            TestOutcome.SKIP: len(
                [r for r in test_results if r.outcome == TestOutcome.SKIP]
            ),
            TestOutcome.XFAIL: len(
                [r for r in test_results if r.outcome == TestOutcome.XFAIL]
            ),
            TestOutcome.XPASS: len(
                [r for r in test_results if r.outcome == TestOutcome.XPASS]
            ),
        }
