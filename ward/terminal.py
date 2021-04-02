import inspect
import os
import platform
import statistics
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from textwrap import dedent, wrap
from typing import (
    Any,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Collection,
)

import itertools
import math
import sys
from rich.console import Console, ConsoleOptions, RenderResult, RenderGroup
from rich.highlighter import NullHighlighter
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.traceback import Traceback
from rich.tree import Tree

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

HORIZONTAL_PAD = (0, 1, 0, 1)

INDENT = " " * 2
BODY_INDENT_SIZE = 4


def make_indent(depth=1):
    return INDENT * depth


DOUBLE_INDENT = make_indent(depth=2)

theme = Theme(
    {
        "title": "bold",
        "heading": "bold",
        "pass": "#ffffff on #137C39",
        "pass.textonly": "#189F4A",
        "fail": "#ffffff on #BF2D2D",
        "fail.textonly": "#BF2D2D",
        "fail.header": "bold #BF2D2D",
        "skip": "#ffffff on #0E67B3",
        "skip.textonly": "#1381E0",
        "xpass": "#162740 on #F4C041",
        "xpass.textonly": "#F4C041",
        "xfail": "#ffffff on #695CC8",
        "xfail.textonly": "#695CC8",
        "muted": "dim",
        "info": "yellow italic",
        "dryrun": "#ffffff on #162740",
        "rule.line": "#189F4A",
        "fixture.name": "bold #1381E0",
        "fixture.scope.test": "bold #189F4A",
        "fixture.scope.module": "bold #F4C041",
        "fixture.scope.global": "bold #EA913C",
        "usedby": "#9285F6",
    }
)
console = Console(theme=theme, highlighter=NullHighlighter())


def format_test_id(test_result: TestResult) -> str:
    """
    Format module name, line number, and test case number
    """
    return f"{format_test_location(test_result.test)}{format_test_case_number(test_result.test)}"


def format_test_location(test: Test) -> str:
    """
    Returns the location of a test as a string of the form '{test.module_name}:{test.line_number}'
    """
    return f"{test.module_name}:{test.line_number}"


def format_test_case_number(test: Test) -> str:
    """
    Returns a string of the format '[{current_test_number}/{num_parameterised_instances}]'.

    For example, for the 3rd run of a test that is parameterised with 5 parameter sets the
    return value is '[3/5]'.
    """
    param_meta = test.param_meta
    if param_meta.group_size > 1:
        pad = len(str(param_meta.group_size))
        iter_indicator = (
            f"[{param_meta.instance_index + 1:>{pad}}/{param_meta.group_size}]"
        )
    else:
        iter_indicator = ""

    return iter_indicator


def output_test_result_line(test_result: TestResult):
    """
    Outputs a single test result to the terminal in Ward's standard output
    format which outputs a single test per line.
    """
    outcome_tag = test_result.outcome.name[:4]

    test = test_result.test
    test_location = format_test_location(test)
    test_case_number = format_test_case_number(test)
    test_style = outcome_to_style(test_result.outcome)

    # Skip/Xfail tests may have a reason note attached that we'll print
    if hasattr(test.marker, "reason") and test.marker.active:
        reason = test.marker.reason
    else:
        reason = ""

    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_column()
    grid.add_column()
    common_columns = (
        Padding(outcome_tag, style=test_style, pad=(0, 1, 0, 1)),
        Padding(f"{test_location}{test_case_number}", style="muted", pad=(0, 1, 0, 1)),
        Padding(
            Markdown(test.description, inline_code_theme="ansi_dark"), pad=(0, 1, 0, 0)
        ),
    )

    if reason:
        grid.add_column(justify="center", style=test_style)
        grid.add_row(
            *common_columns, Padding(reason, pad=(0, 1, 0, 1)),
        )
    else:
        grid.add_row(*common_columns)

    console.print(grid)


def output_test_per_line(fail_limit, test_results_gen):
    num_failures = 0
    all_results = []

    console.print()

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
        console.print()
        for result in test_results_gen:
            all_results.append(result)
            print_dot(result)
            column += 1
            if column == get_terminal_size().width:
                console.print()
                column = 0
            if result.outcome == TestOutcome.FAIL:
                num_failures += 1
            if num_failures == fail_limit:
                break
            sys.stdout.flush()
        console.print()
    except KeyboardInterrupt:
        output_run_cancelled()
    finally:
        return all_results


def print_dot(result):
    style = outcome_to_style(result.outcome)
    console.print(result.outcome.display_char, style=style, end="")


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
                    console.print(
                        rel_path[: final_slash_idx + 1], style="muted", end=""
                    )
                    console.print(rel_path[final_slash_idx + 1 :] + ": ", end="")
                else:
                    console.print(f"\n{rel_path}: ", end="")
            print_dot(result)
            dots_on_line += 1
            if dots_on_line == max_dots_per_line:
                console.print("\n" + " " * (len(rel_path) + 2), end="")
                dots_on_line = 0
            if result.outcome == TestOutcome.FAIL:
                num_failures += 1
            if num_failures == fail_limit:
                break
        console.print()
    except KeyboardInterrupt:
        output_run_cancelled()
    finally:
        return all_results


def output_run_cancelled():
    console.print(
        "Run cancelled - results for tests that ran shown below.", style="info",
    )


@dataclass
class TestTimingStats:
    all_tests_in_session: List[TestResult]
    num_tests_to_show: int

    @property
    def _raw_test_durations_secs(self):
        return [r.test.timer.duration for r in self.all_tests_in_session]

    @property
    def median_secs(self):
        return statistics.median(self._raw_test_durations_secs)

    @property
    def percentile99_secs(self):
        data = self._raw_test_durations_secs
        size = len(data)
        percentile = 99
        return sorted(data)[int(math.ceil((size * percentile) / 100)) - 1]

    def __rich_console__(self, c: Console, co: ConsoleOptions) -> RenderResult:
        test_results = sorted(
            self.all_tests_in_session, key=lambda r: r.test.timer.duration, reverse=True
        )
        grid = Table.grid(padding=(0, 2, 0, 0))
        grid.add_column(justify="right")  # Time taken
        grid.add_column()  # Test ID
        grid.add_column()  # Test description

        for result in test_results[: self.num_tests_to_show]:
            time_taken_secs = result.test.timer.duration
            time_taken_millis = time_taken_secs * 1000
            test_id = format_test_id(result)
            description = result.test.description
            grid.add_row(
                f"[b]{time_taken_millis:.0f}[/b]ms",
                Text(test_id, style="muted"),
                description,
            )

        num_slowest_displayed = min(
            len(self.all_tests_in_session), self.num_tests_to_show
        )
        panel = Panel(
            RenderGroup(
                Padding(
                    f"Median: [b]{self.median_secs * 1000:.2f}[/b]ms"
                    f" [muted]|[/muted] "
                    f"99th Percentile: [b]{self.percentile99_secs * 1000:.2f}[/b]ms",
                    pad=(0, 0, 1, 0),
                ),
                grid,
            ),
            title=f"[b white]{num_slowest_displayed} Slowest Tests[/b white]",
            style="none",
            border_style="rule.line",
        )

        yield panel


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
        console.print(Rule(Text(f"Ward {__version__}", style="title")),)
        if self.config_path:
            try:
                path = self.config_path.relative_to(Path.cwd())
            except ValueError:
                path = self.config_path.name
            console.print(f"Loaded config from [b]{path}[/b].")
        console.print(
            f"Found [b]{self.suite.num_tests}[/b] tests "
            f"and [b]{len(_DEFINED_FIXTURES)}[/b] fixtures "
            f"in [b]{time_to_collect:.2f}[/b] seconds."
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
        failed_test_results = [r for r in all_results if r.outcome == TestOutcome.FAIL]
        for failure in failed_test_results:
            self.output_why_test_failed_header(failure)
            self.output_test_failed_location(failure)
            self.output_why_test_failed(failure)
            self.output_captured_stderr(failure)
            self.output_captured_stdout(failure)
        if failed_test_results:
            self.print_divider()
        else:
            console.print()
        return all_results

    def print_divider(self) -> None:
        console.print(Rule(style="muted"))

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

    def output_captured_stderr(self, test_result: TestResult):
        raise NotImplementedError()

    def output_captured_stdout(self, test_result: TestResult):
        raise NotImplementedError()

    def output_test_failed_location(self, test_result: TestResult):
        raise NotImplementedError()


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
        console.print(
            Padding(
                Rule(
                    title=Text(test.description, style="fail.header"),
                    style="fail.textonly",
                ),
                pad=(1, 0, 0, 0),
            ),
        )

    def output_why_test_failed(self, test_result: TestResult):
        err = test_result.error
        if isinstance(err, TestFailure):
            src_lines, line_num = inspect.getsourcelines(test_result.test.fn)

            if err.operator in Comparison:
                src = "".join(src_lines)
                src = Syntax(
                    src,
                    "python",
                    start_line=line_num,
                    line_numbers=True,
                    highlight_lines={err.error_line},
                    background_color="default",
                    theme="ansi_dark",
                )
                src = Padding(src, (1, 0, 1, 4))
                console.print(src)

                if err.operator == Comparison.Equals:
                    self.print_failure_equals(err)
        else:
            self.print_traceback(err)

    def print_failure_equals(self, err: TestFailure):
        diff_msg = Text("LHS", style="pass.textonly")
        diff_msg.append(" vs ", style="default")
        diff_msg.append("RHS", style="fail.textonly")
        diff_msg.append(" shown below", style="default")
        console.print(Padding(diff_msg, pad=(0, 0, 1, 2)))
        diff = make_diff(
            err.lhs,
            err.rhs,
            width=self.terminal_size.width - 24,
            show_symbols=self.show_diff_symbols,
        )
        console.print(Padding(diff, pad=(0, 0, 1, 4)))

    def print_traceback(self, err):
        trace = getattr(err, "__traceback__", "")
        if trace:
            # The first frame contains library internal code which is not
            # relevant to end users, so skip over it.
            trace = trace.tb_next
            tb = Traceback.from_exception(err.__class__, err, trace, show_locals=True)
            console.print(Padding(tb, pad=(0, 4, 1, 4)))
        else:
            console.print(str(err))

    def output_test_result_summary(
        self, test_results: List[TestResult], time_taken: float, show_slowest: int
    ):
        if show_slowest:
            console.print(TestTimingStats(test_results, show_slowest))

        result_table = Table.grid()
        result_table.add_column(justify="right")
        result_table.add_column()
        result_table.add_column()

        outcome_counts = self._get_outcome_counts(test_results)
        test_count = sum(outcome_counts.values())
        result_table.add_row(
            Padding(str(test_count), pad=HORIZONTAL_PAD, style="bold"),
            Padding("Tests Encountered", pad=HORIZONTAL_PAD),
            style="default",
        )
        for outcome, count in outcome_counts.items():
            if count > 0:
                result_table.add_row(
                    Padding(str(count), pad=HORIZONTAL_PAD, style="bold"),
                    Padding(outcome.display_name, pad=HORIZONTAL_PAD),
                    Padding(f"({100 * count / test_count:.1f}%)", pad=HORIZONTAL_PAD),
                    style=outcome_to_style(outcome),
                )

        exit_code = get_exit_code(test_results)
        if exit_code == ExitCode.SUCCESS:
            result_style = "pass.textonly"
        else:
            result_style = "fail.textonly"

        result_summary_panel = Panel(
            result_table,
            title="[b default]Results[/b default]",
            style="none",
            expand=False,
            border_style=result_style,
        )
        console.print(result_summary_panel)

        console.print(
            Rule(
                f"[b]{exit_code.clean_name}[/b] in [b]{time_taken:.2f}[/b] seconds",
                style=result_style,
            )
        )

    def output_captured_stderr(self, test_result: TestResult):
        if test_result.captured_stderr:
            captured_stderr_lines = test_result.captured_stderr.split("\n")
            console.print(Padding(Text(f"Captured stderr"), pad=(0, 0, 1, 2)))
            for line in captured_stderr_lines:
                console.print(Padding(line, pad=(0, 0, 0, 4)))
            console.print()

    def output_captured_stdout(self, test_result: TestResult):
        if test_result.captured_stdout:
            captured_stdout_lines = test_result.captured_stdout.split("\n")
            console.print(Padding(Text(f"Captured stdout"), pad=(0, 0, 1, 2)))
            for line in captured_stdout_lines:
                console.print(Padding(line, pad=(0, 0, 0, 4)))
            console.print()

    def output_test_failed_location(self, test_result: TestResult):
        if isinstance(test_result.error, TestFailure) or isinstance(
            test_result.error, AssertionError
        ):
            console.print(
                Padding(
                    Text(
                        f"Failed at {test_result.test.path.relative_to(Path.cwd())}:{test_result.error.error_line}"
                    ),
                    pad=(1, 0, 0, 2),
                )
            )

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


def outcome_to_style(outcome: TestOutcome) -> str:
    return {
        TestOutcome.PASS: "pass",
        TestOutcome.SKIP: "skip",
        TestOutcome.FAIL: "fail",
        TestOutcome.XFAIL: "xfail",
        TestOutcome.XPASS: "xpass",
        TestOutcome.DRYRUN: "dryrun",
    }[outcome]


def scope_to_style(scope: Scope) -> str:
    return {
        Scope.Test: "fixture.scope.test",
        Scope.Module: "fixture.scope.module",
        Scope.Global: "fixture.scope.global",
    }[scope]


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

    for module, fixtures in group_by(fixtures, key=lambda f: f.module_name).items():
        console.print(Rule(Text(module, style="title")))

        for fixture in fixtures:
            fixture_tree = make_fixture_information_tree(
                fixture,
                used_by_tests=fixture_to_tests[fixture],
                fixtures_to_children=fixtures_to_children,
                fixtures_to_parents=fixtures_to_parents,
                show_scopes=show_scopes,
                show_docstrings=show_docstrings,
                show_dependencies=show_dependencies,
                show_dependency_trees=show_dependency_trees,
            )
            console.print(fixture_tree)


def make_fixture_information_tree(
    fixture: Fixture,
    used_by_tests: Collection[Test],
    fixtures_to_children: _TYPE_FIXTURE_TO_FIXTURES,
    fixtures_to_parents: _TYPE_FIXTURE_TO_FIXTURES,
    show_scopes: bool,
    show_docstrings: bool,
    show_dependencies: bool,
    show_dependency_trees: bool,
) -> Tree:
    root = Tree(label=make_text_for_fixture(fixture, show_scope=show_scopes))

    if show_dependency_trees:
        max_depth = None
    elif show_dependencies:
        max_depth = 1
    else:
        max_depth = 0

    if show_docstrings and fixture.fn.__doc__ is not None:
        root.add(dedent(fixture.fn.__doc__).strip("\n"))

    if show_dependencies or show_dependency_trees:
        if fixtures_to_parents[fixture]:
            depends_on_node = root.add(label="[usedby]depends on fixtures")
            add_fixture_dependencies_to_tree(
                depends_on_node,
                fixture,
                fixtures_to_parents,
                show_scopes=show_scopes,
                max_depth=max_depth,
            )

        if fixtures_to_children[fixture]:
            used_by_node = root.add(label="[usedby]used by fixtures")
            add_fixture_dependencies_to_tree(
                used_by_node,
                fixture,
                fixtures_to_children,
                show_scopes=show_scopes,
                max_depth=max_depth,
            )

        if used_by_tests:
            used_by_tests_node = root.add("[usedby]used directly by tests")
            add_fixture_usages_by_tests_to_tree(used_by_tests_node, used_by_tests)

        if not (used_by_tests or fixtures_to_children[fixture]):
            root.add(f"[usedby]used by [fail]no tests or fixtures")

    return root


def add_fixture_dependencies_to_tree(
    parent: Tree,
    fixture: Fixture,
    fixtures_to_parents_or_children: _TYPE_FIXTURE_TO_FIXTURES,
    show_scopes: bool,
    max_depth: Optional[int],
    depth: int = 0,
) -> None:
    if max_depth is not None and depth >= max_depth:
        return

    this_layer = fixtures_to_parents_or_children[fixture]

    if not this_layer:
        return

    for dep in this_layer:
        node = parent.add(make_text_for_fixture(fixture=dep, show_scope=show_scopes))
        add_fixture_dependencies_to_tree(
            parent=node,
            fixture=dep,
            fixtures_to_parents_or_children=fixtures_to_parents_or_children,
            show_scopes=show_scopes,
            max_depth=max_depth,
            depth=depth + 1,
        )


def add_fixture_usages_by_tests_to_tree(node: Tree, used_by: Iterable[Test]) -> None:
    grouped_used_by = group_by(used_by, key=lambda t: t.description)
    for idx, (description, tests) in enumerate(grouped_used_by.items()):
        test = tests[0]
        loc = format_test_location(test)
        sep = f" [{len(tests)}]" if len(tests) > 1 else ""
        node.add(f"[muted]{loc}{sep}[/muted] {test.description}")


def make_text_for_fixture(fixture: Fixture, show_scope: bool) -> Text:
    text = Text()
    text.append(f"{fixture.path.name}:{fixture.line_number} ", style="dim")
    text.append(fixture.name, style="fixture.name")

    if show_scope:
        text.append(
            f" (scope: {fixture.scope.value})", style=scope_to_style(fixture.scope)
        )

    return text


class ExitCode(Enum):
    SUCCESS = 0
    FAILED = 1
    ERROR = 2
    NO_TESTS_FOUND = 3

    @property
    def clean_name(self):
        return self.name.replace("_", " ")


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
