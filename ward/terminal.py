import inspect
import os
import platform
import traceback
from enum import Enum
from textwrap import indent

import sys
from colorama import Fore, Style
from dataclasses import dataclass
from pathlib import Path
from pygments import highlight
from pygments.formatters.terminal import TerminalFormatter
from pygments.lexers.python import PythonLexer
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.theme import Style as St
from termcolor import colored, cprint
from typing import Any, Dict, Generator, Iterable, List, Optional

from ward._ward_version import __version__
from ward.diff import make_diff
from ward.expect import Comparison, TestFailure
from ward.suite import Suite
from ward.testing import TestOutcome, TestResult

INDENT = " " * 2
DOUBLE_INDENT = INDENT * 2

console = Console()
console.push_styles({
    "pass-tag": St.parse("grey85 on dark_green bold"),
    "fail-tag": St.parse("black on red bold"),
    "skip-tag": St.parse("bright_white on dodger_blue1 bold"),
    "xfail-tag": St.parse("grey85 on dark_magenta bold"),
    "xpass-tag": St.parse("black on gold1 bold"),
    "dryrun-tag": St.parse("black on green bold"),
    "test-location": St.parse("grey46"),
    "skip-reason": St.parse("italic blue"),
    "xfail-reason": St.parse("italic magenta"),
    "ward-header": St.parse("bold"),
})


def print_no_break(e: Any):
    print(e, end="")


def format_test_id(test_result: TestResult) -> (str, str):
    """
    Format module name, line number, and test case number
    """
    iter_tag = get_iter_tag(test_result)
    return f"{format_test_location(test_result)}{iter_tag}: "


def format_test_location(test_result: TestResult) -> str:
    return f" {test_result.test.module_name}:{test_result.test.line_number}"


def get_iter_tag(test_result: TestResult) -> str:
    # If we're executing a parameterised test
    param_meta = test_result.test.param_meta
    if param_meta.group_size > 1:
        pad = len(str(param_meta.group_size))
        iter_indicator = f" [{param_meta.instance_index + 1:>{pad}}/{param_meta.group_size}]"
    else:
        iter_indicator = ""

    return iter_indicator


def output_test_result_line(test_result: TestResult):
    theme = outcome_to_theme(test_result.outcome)
    outcome = f"{test_result.outcome.name[:4]}"
    description = test_result.test.description
    location = format_test_id(test_result)
    reason = ""

    if test_result.outcome in (TestOutcome.SKIP, TestOutcome.XFAIL):
        reason = test_result.test.marker.reason or ""
        if reason:
            reason = f"     \u2514 reason = {reason}"

    table = Table(show_header=False, padding=0, show_edge=False, box=0)
    table.add_column("outcome", style=theme, width=6, justify="center")
    table.add_column("location", style="test-location", no_wrap=True)
    table.add_column("description")

    table.add_row(outcome, Text(location), Text(f"{description} "))
    console.print(table, highlight=False)
    if reason:
        style = "skip-reason" if test_result.outcome == TestOutcome.SKIP else "xfail-reason"
        console.print(Text(reason), style=style, highlight=False)


def output_test_per_line(fail_limit, test_results_gen):
    num_failures = 0
    all_results = []
    print()
    try:
        for result in test_results_gen:
            output_test_result_line(result)
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
    if result.outcome == TestOutcome.PASS:
        console.print(".", end="", style="green")
    elif result.outcome == TestOutcome.FAIL:
        console.print(Text("F", style="red", end=""), end="")
    elif result.outcome == TestOutcome.XPASS:
        console.print(Text("U", style="magenta"), end="")
    elif result.outcome == TestOutcome.XFAIL:
        console.print(Text("x", style="yellow"), end="")
    elif result.outcome == TestOutcome.SKIP:
        console.print(Text("s", style="blue"), end="")


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
                console.print()
                current_path = result.test.path
                rel_path = str(current_path.relative_to(os.getcwd()))
                max_dots_per_line = (
                    get_terminal_size().width - len(rel_path) - 2
                )  # subtract 2 for ": "
                final_slash_idx = rel_path.rfind("/")
                if final_slash_idx != -1:
                    console.print(Text(rel_path[: final_slash_idx + 1].replace("/", ".")), end="", style="test-location")
                    console.print(Text(current_path.stem), end=": ")
                else:
                    console.print(f"\n{rel_path}: ")
            print_dot(result)
            dots_on_line += 1
            if dots_on_line == max_dots_per_line:
                console.print("\n" + " " * (len(rel_path) + 2))
                dots_on_line = 0
            if result.outcome == TestOutcome.FAIL:
                num_failures += 1
            if num_failures == fail_limit:
                break
    except KeyboardInterrupt:
        output_run_cancelled()
    finally:
        console.print()
        return all_results


def output_run_cancelled():
    cprint(
        "\n[WARD] Run cancelled - results for tests that ran shown below.",
        color="yellow",
    )


class TestResultWriterBase:
    runtime_output_strategies = {
        "test-per-line": output_test_per_line,
        "dots-global": output_dots_global,
        "dots-module": output_dots_module,
    }

    def __init__(
        self, suite: Suite, test_output_style: str, config_path: Optional[Path]
    ):
        self.suite = suite
        self.test_output_style = test_output_style
        self.config_path = config_path
        self.terminal_size = get_terminal_size()

    def output_all_test_results(
        self,
        test_results_gen: Generator[TestResult, None, None],
        time_to_collect: float,
        fail_limit: Optional[int] = None,
    ) -> List[TestResult]:
        python_impl = platform.python_implementation()
        python_version = platform.python_version()
        console.print(
            Text(f"Ward {__version__}, {python_impl} {python_version}\n", style="ward-header")
        )
        if self.config_path:
            try:
                path = self.config_path.relative_to(Path.cwd())
            except ValueError:
                path = self.config_path.name
            console.print(f"Using config from {path}")
            console.print(
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
            self.output_test_failed_location(failure)

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
        self, test_results: List[TestResult], time_taken: float, duration: int
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

    def output_test_failed_location(self, test_result: TestResult):
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
            name_or_desc = test.description
        else:
            name_or_desc = test.qualified_name

        name_or_desc = colored(name_or_desc)
        failure_heading = (
            colored("Failure: ", color="cyan", attrs=["bold"]) + name_or_desc + "\n"
        )
        print(indent(failure_heading, INDENT))

    def output_why_test_failed(self, test_result: TestResult):
        err = test_result.error
        if isinstance(err, TestFailure):
            src_lines, line_num = inspect.getsourcelines(test_result.test.fn)

            # TODO: Only include lines up to where the failure occurs
            if src_lines[-1].strip() == "":
                src_lines = src_lines[:-1]

            gutter_width = len(str(len(src_lines) + line_num))

            def gutter(i):
                offset_line_num = i + line_num
                rv = f"{str(offset_line_num):>{gutter_width}}"
                if offset_line_num == err.error_line:
                    return colored(f"{rv} ! ", color="red")
                else:
                    return lightblack(f"{rv} | ")

            if err.operator in Comparison:
                src = "".join(src_lines)
                src = highlight(src, PythonLexer(), TerminalFormatter())
                src = f"".join(
                    [gutter(i) + l for i, l in enumerate(src.splitlines(keepends=True))]
                )
                print(indent(src, DOUBLE_INDENT))

                if err.operator == Comparison.Equals:
                    self.print_failure_equals(err)
        else:
            self.print_traceback(err)

        print(Style.RESET_ALL)

    def print_failure_equals(self, err: TestFailure):
        diff_msg = (
            f"{colored('Comparison:', color='cyan', attrs=['bold'])} {colored('LHS', color='green')}"
            f" vs {colored('RHS', color='red')} shown below\n"
        )
        print(indent(diff_msg, INDENT))
        diff = make_diff(err.lhs, err.rhs, width=self.terminal_size.width - 24)
        print(indent(diff, DOUBLE_INDENT))

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

    def result_checkbox(self, expect):
        if expect.success:
            result_marker = f"[ {Fore.GREEN}okay{Style.RESET_ALL} ]{Fore.GREEN}"
        else:
            result_marker = f"[ {Fore.RED}fail{Style.RESET_ALL} ]{Fore.RED}"
        return result_marker

    def output_test_result_summary(
        self, test_results: List[TestResult], time_taken: float, show_slowest: int
    ):
        if show_slowest:
            self._output_slowest_tests(test_results, show_slowest)
        outcome_counts = self._get_outcome_counts(test_results)

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
        if outcome_counts[TestOutcome.DRYRUN]:
            output += f"{colored(str(outcome_counts[TestOutcome.DRYRUN]) + ' printed', color='green')}"

        if test_results:
            output += " ] "

        print(output)

    def _output_slowest_tests(self, test_results: List[TestResult], num_tests: int):
        test_results = sorted(
            test_results, key=lambda r: r.test.timer.duration, reverse=True
        )
        self.print_divider()
        heading = f"{colored('Longest Running Tests:', color='cyan', attrs=['bold'])}\n"
        print(indent(heading, INDENT))
        for result in test_results[:num_tests]:
            test_id = format_test_id(result)
            message = f"{result.test.timer.duration:.2f} sec {test_id} {result.test.description} "
            print(indent(message, DOUBLE_INDENT))
        print()

    def output_captured_stderr(self, test_result: TestResult):
        if test_result.captured_stderr:
            captured_stderr_lines = test_result.captured_stderr.split("\n")
            print(
                indent(
                    colored(f"Captured stderr:\n", color="cyan", attrs=["bold"]), INDENT
                )
            )
            for line in captured_stderr_lines:
                print(indent(line, DOUBLE_INDENT))
            print()

    def output_captured_stdout(self, test_result: TestResult):
        if test_result.captured_stdout:
            captured_stdout_lines = test_result.captured_stdout.split("\n")
            print(
                indent(
                    colored(f"Captured stdout:\n", color="cyan", attrs=["bold"]), INDENT
                )
            )
            for line in captured_stdout_lines:
                print(indent(line, DOUBLE_INDENT))

    def output_test_failed_location(self, test_result: TestResult):
        if isinstance(test_result.error, TestFailure) or isinstance(
            test_result.error, AssertionError
        ):
            print(
                indent(colored("Location:", color="cyan", attrs=["bold"]), INDENT),
                f"{test_result.test.path.relative_to(Path.cwd())}:{test_result.error.error_line}",
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
            TestOutcome.DRYRUN: len(
                [r for r in test_results if r.outcome == TestOutcome.DRYRUN]
            ),
        }


def outcome_to_theme(outcome: TestOutcome) -> str:
    return {
        TestOutcome.PASS: "pass-tag",
        TestOutcome.SKIP: "skip-tag",
        TestOutcome.FAIL: "fail-tag",
        TestOutcome.XFAIL: "xfail-tag",
        TestOutcome.XPASS: "xpass-tag",
        TestOutcome.DRYRUN: "dryrun-tag",
    }[outcome]


class ExitCode(Enum):
    SUCCESS = 0
    FAILED = 1
    ERROR = 2
    NO_TESTS_FOUND = 3


def get_exit_code(results: Iterable[TestResult]) -> ExitCode:
    if not results:
        return ExitCode.NO_TESTS_FOUND

    if any(
        r.outcome == TestOutcome.FAIL or r.outcome == TestOutcome.XPASS for r in results
    ):
        exit_code = ExitCode.FAILED
    else:
        exit_code = ExitCode.SUCCESS
    return exit_code
