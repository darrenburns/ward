import inspect
import os
import platform
import sys
import traceback
import itertools
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from textwrap import indent, dedent, wrap
from typing import (
    Any,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Iterator,
    Collection,
)

from colorama import Fore, Style
from pygments import highlight
from pygments.formatters.terminal import TerminalFormatter
from pygments.lexers.python import PythonLexer
from termcolor import colored, cprint

from ward._ward_version import __version__
from ward.diff import make_diff
from ward.expect import Comparison, TestFailure
from ward.fixtures import (
    Fixture,
    Scope,
    _DEFINED_FIXTURES,
    fixture_parents_and_children,
    _TYPE_FIXTURE_TO_FIXTURES,
)
from ward.testing import Test, fixtures_used_directly_by_tests
from ward.testing import TestOutcome, TestResult
from ward.util import group_by

INDENT = " " * 2


def make_indent(depth=1):
    return INDENT * depth


DOUBLE_INDENT = make_indent(depth=2)


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


def format_test_id(test_result: TestResult) -> (str, str):
    """
    Format module name, line number, and test case number
    """

    test_id = lightblack(
        f"{format_test_location(test_result.test)}{format_test_case_number(test_result)}:"
    )

    return test_id


def format_test_location(test: Test) -> str:
    return f"{test.module_name}:{test.line_number}"


def format_test_case_number(test_result: TestResult) -> str:
    # If we're executing a parameterised test
    param_meta = test_result.test.param_meta
    if param_meta.group_size > 1:
        pad = len(str(param_meta.group_size))
        iter_indicator = (
            f" [{param_meta.instance_index + 1:>{pad}}/{param_meta.group_size}]"
        )
    else:
        iter_indicator = ""

    return iter_indicator


def output_test_result_line(test_result: TestResult):
    colour = outcome_to_colour(test_result.outcome)
    bg = f"on_{colour}"
    padded_outcome = f" {test_result.outcome.name[:4]} "

    iter_indicator = format_test_case_number(test_result)
    mod_name = format_test_id(test_result)
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
        self,
        suite,
        test_output_style: str,
        config_path: Optional[Path],
        show_diff_symbols: bool = False,
    ):
        self.suite = suite
        self.test_output_style = test_output_style
        self.config_path = config_path
        self.show_diff_symbols = show_diff_symbols
        self.terminal_size = get_terminal_size()

    def output_header(self, time_to_collect):
        python_impl = platform.python_implementation()
        python_version = platform.python_version()
        print(f"Ward {__version__}, {python_impl} {python_version}")
        if self.config_path:
            try:
                path = self.config_path.relative_to(Path.cwd())
            except ValueError:
                path = self.config_path.name
            print(f"Using config from {path}")
        print(
            f"Collected {self.suite.num_tests} tests "
            f"and {len(_DEFINED_FIXTURES)} fixtures "
            f"in {time_to_collect:.2f} seconds."
        )

    def output_all_test_results(
        self,
        test_results_gen: Generator[TestResult, None, None],
        fail_limit: Optional[int] = None,
    ) -> List[TestResult]:
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
        diff = make_diff(
            err.lhs,
            err.rhs,
            width=self.terminal_size.width - 24,
            show_symbols=self.show_diff_symbols,
        )
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


def outcome_to_colour(outcome: TestOutcome) -> str:
    return {
        TestOutcome.PASS: "green",
        TestOutcome.SKIP: "blue",
        TestOutcome.FAIL: "red",
        TestOutcome.XFAIL: "magenta",
        TestOutcome.XPASS: "yellow",
        TestOutcome.DRYRUN: "green",
    }[outcome]


def scope_to_colour(scope: Scope) -> str:
    return {Scope.Test: "green", Scope.Module: "blue", Scope.Global: "magenta"}[scope]


def output_fixtures(
    fixtures: List[Fixture],
    tests: List[Test],
    show_scopes: bool,
    show_docstrings: bool,
    show_dependencies: bool,
    show_dependency_trees: bool,
):
    generated_tests = itertools.chain.from_iterable(
        test.get_parameterised_instances() for test in tests
    )

    fixture_to_tests = fixtures_used_directly_by_tests(generated_tests)

    fixtures_to_parents, fixtures_to_children = fixture_parents_and_children(fixtures)

    for fixture in fixtures:
        output_fixture_information(
            fixture,
            used_by_tests=fixture_to_tests[fixture],
            fixtures_to_children=fixtures_to_children,
            fixtures_to_parents=fixtures_to_parents,
            show_scopes=show_scopes,
            show_docstrings=show_docstrings,
            show_dependencies=show_dependencies,
            show_dependency_trees=show_dependency_trees,
        )


def output_fixture_information(
    fixture: Fixture,
    used_by_tests: Collection[Test],
    fixtures_to_children: _TYPE_FIXTURE_TO_FIXTURES,
    fixtures_to_parents: _TYPE_FIXTURE_TO_FIXTURES,
    show_scopes: bool,
    show_docstrings: bool,
    show_dependencies: bool,
    show_dependency_trees: bool,
):
    lines = [format_fixture(fixture, show_scope=show_scopes)]

    if show_dependency_trees:
        max_depth = None
    elif show_dependencies:
        max_depth = 1
    else:
        max_depth = 0

    if show_dependencies or show_dependency_trees:
        if fixtures_to_parents[fixture]:
            lines.append(indent("depends on fixtures", INDENT))
            lines.extend(
                yield_fixture_dependency_tree(
                    fixture,
                    fixtures_to_parents,
                    show_scopes=show_scopes,
                    max_depth=max_depth,
                )
            )
            lines.append("")

        if fixtures_to_children[fixture]:
            lines.append(indent("used by fixtures", INDENT))
            lines.extend(
                yield_fixture_dependency_tree(
                    fixture,
                    fixtures_to_children,
                    show_scopes=show_scopes,
                    max_depth=max_depth,
                )
            )
            lines.append("")

        if used_by_tests:
            lines.append(indent("used directly by tests", INDENT))
            lines.extend(yield_fixture_usages_by_tests(used_by_tests))
            lines.append("")

        if not (used_by_tests or fixtures_to_children[fixture]):
            lines.append(
                indent(
                    f"used by {colored('no tests or fixtures', color='red', attrs=['bold'])}",
                    INDENT,
                )
            )
            lines.append("")

    if show_docstrings and fixture.fn.__doc__ is not None:
        doc = dedent(fixture.fn.__doc__.strip("\n"))
        lines.extend(indent(doc, INDENT).splitlines())
        lines.append("")

    print("\n".join(lines))


def yield_fixture_usages_by_tests(used_by: List[Test]) -> Iterator[str]:
    grouped_used_by = group_by(used_by, key=lambda t: t.description)
    for idx, (description, tests) in enumerate(grouped_used_by.items()):
        test = tests[0]
        prefix = "├─" if idx != len(grouped_used_by) - 1 else "└─"
        loc = lightblack(format_test_location(test))
        sep = lightblack(f" [{len(tests)}]:" if len(tests) > 1 else ":")
        yield indent(
            f"{prefix} {loc}{sep} {test.description}", INDENT,
        )


def yield_fixture_dependency_tree(
    fixture: Fixture,
    fixtures_to_parents_or_children: _TYPE_FIXTURE_TO_FIXTURES,
    show_scopes: bool,
    max_depth: Optional[int],
    depth: int = 0,
    prefix=INDENT,
) -> Iterator[str]:
    if max_depth is not None and depth >= max_depth:
        return

    this_layer = fixtures_to_parents_or_children[fixture]

    if not this_layer:
        return

    for idx, dep in enumerate(this_layer):
        fix = format_fixture(dep, show_scopes)
        if idx < len(this_layer) - 1:
            tree = "├─"
            next_prefix = prefix + "│  "
        else:
            tree = "└─"
            next_prefix = prefix + "   "

        yield f"{prefix}{tree} {fix}"
        yield from yield_fixture_dependency_tree(
            dep,
            fixtures_to_parents_or_children,
            show_scopes,
            max_depth,
            depth=depth + 1,
            prefix=next_prefix,
        )


def format_fixture(fixture: Fixture, show_scope: bool):
    path = lightblack(f"{fixture.path.name}:{fixture.line_number}")
    name = colored(fixture.name, color="cyan", attrs=["bold"])
    scope = colored(
        fixture.scope.value, color=scope_to_colour(fixture.scope), attrs=["bold"]
    )
    header = f"{path} {name}"

    if show_scope:
        header = f"{header} (scope: {scope})"

    return header


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
