import sys
import traceback
from dataclasses import dataclass
from enum import Enum
from itertools import cycle
from typing import Generator, List, Tuple, Optional

from blessings import Terminal
from colorama import Fore, Style, Back

from ward.diff import build_unified_diff, build_auto_diff
from ward.expect import ExpectationFailed
from ward.fixtures import TestSetupError
from ward.suite import Suite
from ward.test_result import TestResult, TestOutcome


def truncate(s: str, num_chars: int) -> str:
    suffix = "..." if len(s) > num_chars - 3 else ""
    return s[:num_chars] + suffix


def write_test_failure_output(term, test_result):
    # Header of failure output
    test_name = test_result.test.name
    test_module = test_result.test.module.__name__
    test_result_heading = f"{Fore.BLACK}{Back.RED}◤ {test_module}.{test_name} failed: "
    write_over_line(f"{test_result_heading}{Style.RESET_ALL}", 0, term)
    err = test_result.error
    if term.width:
        width = term.width - 30
    else:
        width = 60

    # Body of failure output, depends on how the test failed
    if isinstance(err, TestSetupError):
        write_over_line(str(err), 0, term)
    elif isinstance(err, ExpectationFailed):
        print()
        write_over_line(
            f"  Given {truncate(repr(err.history[0].this), num_chars=width)}",
            0,
            term,
        )
        print()
        for expect in err.history:
            if expect.success:
                result_marker = f"[ {Fore.GREEN}✓{Style.RESET_ALL} ]{Fore.GREEN}"
            else:
                result_marker = f"[ {Fore.RED}✗{Style.RESET_ALL} ]{Fore.RED}"

            if expect.op == "satisfies" and hasattr(expect.that, "__name__"):
                expect_that = truncate(expect.that.__name__, num_chars=width)
            else:
                expect_that = truncate(repr(expect.that), num_chars=width)
            write_over_line(
                f"    {result_marker} it {expect.op} {expect_that}{Style.RESET_ALL}",
                0,
                term,
            )

        # TODO: Add ability to hook and change the function called below
        # TODO: Diffs should be shown for more than just op == "equals"
        if err.history and err.history[-1].op == "equals":
            expect = err.history[-1]
            print(
                f"\n  Showing diff of {Fore.GREEN}expected value{Fore.RESET} vs {Fore.RED}actual value{Fore.RESET}:\n")
            diff = build_unified_diff(expect.that, expect.this)
            print(diff)
    else:
        trace = getattr(err, "__traceback__", "")
        if trace:
            trc = traceback.format_exception(None, err, trace)
            write_over_line("".join(trc), 0, term)
        else:
            write_over_line(str(err), 0, term)


def write_test_result(test_result: TestResult, term: Terminal):
    write_over_line(str(test_result), 2, term)


def write_over_progress_bar(green_pct: float, red_pct: float, term: Terminal):
    if not term.is_a_tty:
        return

    num_green_bars = int(green_pct * term.width)
    num_red_bars = int(red_pct * term.width)

    # Deal with rounding, converting to int could leave us with 1 bar less, so make it green
    if term.width - num_green_bars - num_red_bars == 1:
        num_green_bars += 1

    bar = term.red("█" * num_red_bars) + term.green("█" * num_green_bars)
    write_over_line(bar, 1, term)


def write_over_line(str_to_write: str, offset_from_bottom: int, term: Terminal):
    # TODO: Smarter way of tracking margins based on escape codes used.
    esc_code_rhs_margin = (
        37
    )  # chars that are part of escape code, but NOT actually printed. Yeah I know...
    with term.location(None, term.height - offset_from_bottom):
        right_margin = (
            max(0, term.width - len(str_to_write) + esc_code_rhs_margin) * " "
        )
        sys.stdout.write(f"{str_to_write}{right_margin}")
        sys.stdout.flush()


def reset_cursor(term: Terminal):
    print(term.normal_cursor())
    print(term.move(term.height - 1, 0))


class ExitCode(Enum):
    SUCCESS = 0
    TEST_FAILED = 1
    ERROR = 2


@dataclass
class TestRunnerWriter:
    suite: Suite
    terminal: Terminal
    test_results: Generator[TestResult, None, None]

    def run_and_write_test_results(self) -> ExitCode:
        print(self.terminal.hide_cursor())
        print("\n")
        write_over_line(
            f"{Fore.CYAN}[ward] Collected {self.suite.num_tests} tests and "
            f"{self.suite.num_fixtures} fixtures.\nRunning tests...",
            4,
            self.terminal,
        )

        failing_test_results = []
        passed, failed, skipped = 0, 0, 0
        spinner = cycle("⠁⠁⠉⠙⠚⠒⠂⠂⠒⠲⠴⠤⠄⠄⠤⠠⠠⠤⠦⠖⠒⠐⠐⠒⠓⠋⠉⠈⠈")
        info_bar = ""
        for result in self.test_results:
            if result.outcome == TestOutcome.PASS:
                passed += 1
            elif result.outcome == TestOutcome.FAIL:
                failed += 1
                failing_test_results.append(result)
            elif result.outcome == TestOutcome.SKIP:
                skipped += 1

            write_test_result(result, self.terminal)

            pass_pct = passed / max(passed + failed, 1)
            fail_pct = 1.0 - pass_pct

            if self.terminal.is_a_tty:
                write_over_progress_bar(pass_pct, fail_pct, self.terminal)

            info_bar = (
                f"{Fore.CYAN}{next(spinner)} "
                f"{passed + failed} tests ran {Fore.LIGHTBLACK_EX}|{Fore.CYAN} "
                f"{failed} tests failed {Fore.LIGHTBLACK_EX}|{Fore.CYAN} "
                f"{passed} tests passed {Fore.LIGHTBLACK_EX}|{Fore.CYAN} "
                f"{pass_pct * 100:.2f}% pass rate{Style.RESET_ALL}"
            )

            write_over_line(info_bar, 0, self.terminal)
        total = passed + failed
        if total == 0:
            write_over_line(
                self.terminal.cyan_bold(f"No tests found."), 1, self.terminal
            )

        reset_cursor(self.terminal)
        if failing_test_results:
            for test_result in failing_test_results:
                write_test_failure_output(self.terminal, test_result)
            print()
            print(info_bar)
            return ExitCode.TEST_FAILED

        return ExitCode.SUCCESS


class TestResultWriterBase:

    def __init__(self, terminal: Terminal, suite: Suite):
        self.terminal = terminal
        self.suite = suite

    def output_all_test_results(
        self,
        test_results_gen: Generator[TestResult, None, None],
        fail_limit: Optional[int] = None,
    ) -> List[TestResult]:
        all_results = []
        failed_test_results = []
        print(f"Ward collected {self.suite.num_tests} tests and {self.suite.num_fixtures} fixtures. {Style.RESET_ALL}")
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

        self.output_test_result_summary(all_results)
        return all_results

    def output_single_test_result(self, test_result: TestResult):
        """Indicate whether a test passed, failed, was skipped etc."""
        raise NotImplementedError()

    def output_why_test_failed_header(self, test_result: TestResult):
        """
        Printed above the failing test output
        """
        raise NotImplementedError()

    def output_test_result_summary(self, test_results: List[TestResult]):
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
                    f"\n  Showing diff of {Fore.GREEN}expected value{Fore.RESET} vs {Fore.RED}actual value{Fore.RESET}:\n")

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

    def output_test_result_summary(self, test_results: List[TestResult]):
        num_passed, num_failed, num_skipped = self._get_num_passed_failed_skipped(test_results)
        if self.terminal.is_a_tty:
            print(self.generate_chart(num_passed=num_passed, num_failed=num_failed, num_skipped=num_skipped))
        print(f"Test run complete [ "
              f"{Fore.RED}{num_failed} failed "
              f"{Fore.YELLOW} {num_skipped} skipped "
              f"{Fore.GREEN} {num_passed} passed"
              f"{Style.RESET_ALL} ]")

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
