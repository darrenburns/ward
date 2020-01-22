import os
import platform
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from textwrap import wrap
from typing import Any, Dict, Generator, List, Optional

from colorama import Fore, Style
from termcolor import colored, cprint

from ward._ward_version import __version__
from ward.diff import make_diff
from ward.expect import ExpectationFailed, Expected
from ward.suite import Suite
from ward.testing import TestOutcome, TestResult
from ward.util import ExitCode, get_exit_code, outcome_to_colour, truncate


def print_no_break(e: Any):
    print(e, end="")


def multiline_description(s: str, indent: int, width: int) -> str:
    wrapped = wrap(s, width)
    if len(wrapped) == 1:
        return wrapped[0]
    rv = wrapped[0]
    for line in wrapped[1:]:
        indent_str = " " * indent
        rv += f"\n{indent_str}{line}"
    return rv


def output_test_result_line(test_result: TestResult):
    colour = outcome_to_colour(test_result.outcome)
    bg = f"on_{colour}"
    padded_outcome = f" {test_result.outcome.name[:4]} "

    # If we're executing a parameterised test
    param_meta = test_result.test.param_meta
    if param_meta.group_size > 1:
        iter_indicator = f" [{param_meta.instance_index + 1}/{param_meta.group_size}]"
    else:
        iter_indicator = ""

    mod_name = lightblack(
        f"{test_result.test.module_name}:"
        f"{test_result.test.line_number}"
        f"{iter_indicator}:"
    )
    if (
        test_result.outcome == TestOutcome.SKIP
        or test_result.outcome == TestOutcome.XFAIL
    ):
        reason = test_result.test.marker.reason or ""
        if reason:
            reason = lightblack(f" [{reason}]")
    else:
        reason = ""

    name_or_desc = test_result.test.description
    indent = (
        len(padded_outcome)
        + len(test_result.test.module_name)
        + len(str(test_result.test.line_number))
        + len(iter_indicator)
        + 4
    )
    width = get_terminal_size().width - indent
    print(
        colored(padded_outcome, color="grey", on_color=bg),
        mod_name,
        multiline_description(name_or_desc + reason, indent=indent, width=width),
    )


def output_test_per_line(fail_limit, test_results_gen):
    num_failures = 0
    all_results = []
    print()
    try:
        for result in test_results_gen:
            output_test_result_line(result)
            sys.stdout.write(Style.RESET_ALL)
            all_results.append(result)
            if result.outcome == TestOutcome.FAIL:
                num_failures += 1
            if num_failures == fail_limit:
                break
    except KeyboardInterrupt:
        output_run_cancelled()
    finally:
        return all_results


def output_dots_global(
    fail_limit: int, test_results_gen: Generator[TestResult, None, None]
) -> List[TestResult]:
    column = 0
    num_failures = 0
    all_results = []
    try:
        print()
        for result in test_results_gen:
            all_results.append(result)
            print_dot(result)
            column += 1
            if column == get_terminal_size().width:
                print()
                column = 0
            if result.outcome == TestOutcome.FAIL:
                num_failures += 1
            if num_failures == fail_limit:
                break
            sys.stdout.flush()
        print()
    except KeyboardInterrupt:
        output_run_cancelled()
    finally:
        return all_results


def print_dot(result):
    colour = outcome_to_colour(result.outcome)
    if result.outcome == TestOutcome.PASS:
        print_no_break(colored(".", color=colour))
    elif result.outcome == TestOutcome.FAIL:
        print_no_break(colored("F", color=colour))
    elif result.outcome == TestOutcome.XPASS:
        print_no_break(colored("U", color=colour))
    elif result.outcome == TestOutcome.XFAIL:
        print_no_break(colored("x", color=colour))
    elif result.outcome == TestOutcome.SKIP:
        print_no_break(colored("s", color=colour))


def output_dots_module(
    fail_limit: int, test_results_gen: Generator[TestResult, None, None]
) -> List[TestResult]:
    current_path = Path("")
    rel_path = ""
    dots_on_line = 0
    num_failures = 0
    max_dots_per_line = get_terminal_size().width - 40
    all_results = []
    try:
        for result in test_results_gen:
            all_results.append(result)
            if result.test.path != current_path:
                dots_on_line = 0
                print()
                current_path = result.test.path
                rel_path = str(current_path.relative_to(os.getcwd()))
                max_dots_per_line = (
                    get_terminal_size().width - len(rel_path) - 2
                )  # subtract 2 for ": "
                final_slash_idx = rel_path.rfind("/")
                if final_slash_idx != -1:
                    print_no_break(
                        lightblack(rel_path[: final_slash_idx + 1])
                        + rel_path[final_slash_idx + 1 :]
                        + ": "
                    )
                else:
                    print_no_break(f"\n{rel_path}: ")
            print_dot(result)
            dots_on_line += 1
            if dots_on_line == max_dots_per_line:
                print_no_break("\n" + " " * (len(rel_path) + 2))
                dots_on_line = 0
            if result.outcome == TestOutcome.FAIL:
                num_failures += 1
            if num_failures == fail_limit:
                break
            sys.stdout.flush()
        print()
    except KeyboardInterrupt:
        output_run_cancelled()
    finally:
        return all_results


def output_run_cancelled():
    cprint(
        "\n[WARD] Run cancelled - " "results for tests that ran shown below.",
        color="yellow",
    )


class TestResultWriterBase:
    runtime_output_strategies = {
        "test-per-line": output_test_per_line,
        "dots-global": output_dots_global,
        "dots-module": output_dots_module,
    }

    def __init__(self, suite: Suite, test_output_style: str):
        self.suite = suite
        self.test_output_style = test_output_style
        self.terminal_size = get_terminal_size()

    def output_all_test_results(
        self,
        test_results_gen: Generator[TestResult, None, None],
        time_to_collect: float,
        fail_limit: Optional[int] = None,
    ) -> List[TestResult]:
        python_impl = platform.python_implementation()
        python_version = platform.python_version()
        print(
            f"Ward {__version__}, {python_impl} {python_version}\n"
            f"Collected {self.suite.num_tests} tests "
            f"in {time_to_collect:.2f} seconds."
        )
        if not self.suite.num_tests:
            return []
        output_tests = self.runtime_output_strategies.get(
            self.test_output_style, output_test_per_line
        )
        all_results = output_tests(fail_limit, test_results_gen)
        self.output_test_run_post_failure_summary(test_results=all_results)
        failed_test_results = [r for r in all_results if r.outcome == TestOutcome.FAIL]
        for failure in failed_test_results:
            self.print_divider()
            self.output_why_test_failed_header(failure)
            self.output_why_test_failed(failure)
            self.output_captured_stderr(failure)
            self.output_captured_stdout(failure)

        if failed_test_results:
            self.print_divider()
        else:
            print()
        return all_results

    def print_divider(self):
        print(lightblack(f"{'_' * self.terminal_size.width}\n"))

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
            for line in trc:
                sublines = line.split("\n")
                for subline in sublines:
                    content = " " * 4 + subline
                    if subline.lstrip().startswith('File "'):
                        cprint(content, color="blue")
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
            result_marker = f"[ {Fore.GREEN}okay{Style.RESET_ALL} ]{Fore.GREEN}"
        else:
            result_marker = f"[ {Fore.RED}fail{Style.RESET_ALL} ]{Fore.RED}"
        return result_marker

    def output_test_result_summary(
        self, test_results: List[TestResult], time_taken: float
    ):
        outcome_counts = self._get_outcome_counts(test_results)
        if test_results:
            chart = self.generate_chart(
                num_passed=outcome_counts[TestOutcome.PASS],
                num_failed=outcome_counts[TestOutcome.FAIL],
                num_skipped=outcome_counts[TestOutcome.SKIP],
                num_xfail=outcome_counts[TestOutcome.XFAIL],
                num_unexp=outcome_counts[TestOutcome.XPASS],
            )
            print(chart, "")

        exit_code = get_exit_code(test_results)
        if exit_code == ExitCode.SUCCESS:
            result = colored(exit_code.name, color="green")
        else:
            result = colored(exit_code.name, color="red")

        output = f"{result} in {time_taken:.2f} seconds"
        if test_results:
            output += " [ "

        if outcome_counts[TestOutcome.FAIL]:
            output += f"{colored(str(outcome_counts[TestOutcome.FAIL]) + ' failed', color='red')}  "
        if outcome_counts[TestOutcome.XPASS]:
            output += f"{colored(str(outcome_counts[TestOutcome.XPASS]) + ' xpassed', color='yellow')}  "
        if outcome_counts[TestOutcome.XFAIL]:
            output += f"{colored(str(outcome_counts[TestOutcome.XFAIL]) + ' xfailed', color='magenta')}  "
        if outcome_counts[TestOutcome.SKIP]:
            output += f"{colored(str(outcome_counts[TestOutcome.SKIP]) + ' skipped', color='blue')}  "
        if outcome_counts[TestOutcome.PASS]:
            output += f"{colored(str(outcome_counts[TestOutcome.PASS]) + ' passed', color='green')}"

        if test_results:
            output += " ] "

        print(output)

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
