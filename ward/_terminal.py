import abc
import inspect
import itertools
import math
import os
import platform
import statistics
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from textwrap import dedent
from typing import (
    Collection,
    Dict,
    Generator,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
)

from rich.console import (
    Console,
    ConsoleOptions,
    RenderableType,
    RenderGroup,
    RenderResult,
)
from rich.highlighter import NullHighlighter
from rich.live import Live
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.pretty import Pretty
from rich.progress import (
    BarColumn,
    Progress,
    RenderableColumn,
    SpinnerColumn,
    TimeElapsedColumn,
)
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.traceback import Traceback
from rich.tree import Tree

from ward._diff import Diff
from ward._fixtures import FixtureHierarchyMapping, fixture_parents_and_children
from ward._suite import Suite
from ward._utilities import group_by
from ward._ward_version import __version__
from ward.expect import Comparison, TestFailure
from ward.fixtures import Fixture
from ward.models import ExitCode, Scope
from ward.testing import Test, TestOutcome, TestResult, fixtures_used_directly_by_tests

HORIZONTAL_PAD = (0, 1, 0, 1)

INDENT = " " * 2

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
rich_console = Console(theme=theme, highlighter=NullHighlighter())


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


class TestOutputStyle(str, Enum):
    TEST_PER_LINE = "test-per-line"
    DOTS_GLOBAL = "dots-global"
    DOTS_MODULE = "dots-module"
    LIVE = "live"
    NONE = "none"


class TestProgressStyle(str, Enum):
    INLINE = "inline"
    BAR = "bar"
    NONE = "none"


def get_test_result_line(
    test_result: TestResult,
    test_index: int,
    num_tests: int,
    progress_styles: List[TestProgressStyle],
    extra_left_pad: int = 0,
) -> Table:
    """
    Outputs a single test result to the terminal in Ward's standard output
    format which outputs a single test per line.
    """
    outcome_tag = test_result.outcome.name[:4]

    test = test_result.test
    test_location = format_test_location(test)
    test_case_number = format_test_case_number(test)
    test_style = outcome_to_style(test_result.outcome)

    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_column()
    grid.add_column()
    columns = [
        Padding(outcome_tag, style=test_style, pad=(0, 1, 0, 1 + extra_left_pad)),
        Padding(f"{test_location}{test_case_number}", style="muted", pad=(0, 1, 0, 1)),
        Padding(
            Markdown(test.description, inline_code_theme="ansi_dark"), pad=(0, 1, 0, 0)
        ),
    ]

    # Skip/Xfail tests may have a reason note attached that we'll print
    reason = getattr(test.marker, "reason", "")
    if reason and test.marker.active:
        grid.add_column(justify="center", style=test_style)
        columns.append(Padding(reason, pad=(0, 1, 0, 1)))

    if TestProgressStyle.INLINE in progress_styles:
        grid.add_column(justify="right", style="muted")
        columns.append(f"{(test_index + 1) / num_tests:>4.0%}")

    grid.add_row(*columns)

    return grid


INLINE_PROGRESS_LEN = 5  # e.g. "  93%"


def get_dot(result: TestResult) -> Text:
    style = outcome_to_style(result.outcome)
    return Text(result.outcome.display_char, style=style, end="")


@dataclass
class TestTimingStatsPanel:
    all_tests_in_session: List[TestResult]
    num_tests_to_show: int

    @property
    def _raw_test_durations_secs(self):
        return [r.test.timer.duration for r in self.all_tests_in_session]

    @property
    def _median_secs(self):
        return statistics.median(self._raw_test_durations_secs)

    @property
    def _percentile99_secs(self):
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
                    f"Median: [b]{self._median_secs * 1000:.2f}[/b]ms"
                    f" [muted]|[/muted] "
                    f"99th Percentile: [b]{self._percentile99_secs * 1000:.2f}[/b]ms",
                    pad=(0, 0, 1, 0),
                ),
                grid,
            ),
            title=f"[b white]{num_slowest_displayed} Slowest Tests[/b white]",
            style="none",
            border_style="rule.line",
        )

        yield panel


@dataclass
class SessionPrelude:
    time_to_collect_secs: float
    num_tests_collected: int
    num_fixtures_collected: int
    config_path: Optional[Path]
    python_impl: str = field(default=platform.python_implementation())
    python_version: str = field(default=platform.python_version())
    ward_version: str = field(default=__version__)

    def __rich_console__(self, c: Console, co: ConsoleOptions) -> RenderResult:
        yield Rule(
            Text(
                f"Ward {self.ward_version} | {self.python_impl} {self.python_version}",
                style="title",
            )
        )
        if self.config_path:
            try:
                path = self.config_path.relative_to(Path.cwd())
            except ValueError:
                path = self.config_path.name
            yield f"Loaded config from [b]{path}[/b]."

        yield (
            f"Found [b]{self.num_tests_collected}[/b] tests "
            f"and [b]{self.num_fixtures_collected}[/b] fixtures "
            f"in [b]{self.time_to_collect_secs:.2f}[/b] seconds."
        )


class ResultProcessor(abc.ABC):
    @abc.abstractmethod
    def handle_result(self, test_result: TestResult):
        pass


class TerminalResultProcessor(ResultProcessor):
    def __init__(
        self,
        suite: Suite,
        test_output_style: str,
        progress_styles: List[TestProgressStyle],
        config_path: Optional[Path],
        show_diff_symbols: bool = False,
    ):
        self.suite = suite
        self.test_output_style = test_output_style
        self.progress_styles = progress_styles
        self.config_path = config_path
        self.show_diff_symbols = show_diff_symbols

    def handle_result(self, test_result: TestResult):
        # Make the actual output of the result a pluggy hook, so that users can implement their own version
        pass


class TestResultDisplayWidget:
    def __init__(self, num_tests: int, progress_styles: List[TestProgressStyle]):
        self.console = rich_console
        self.num_tests = num_tests
        self.progress_styles = progress_styles

    def footer(self, test_results: List[TestResult]) -> Optional[RenderableType]:
        """
        This method should return an object that can be rendered by Rich.
        It will be inserted into the "footer" of the test suite result display,
        which hugs the bottom of the output as the suite runs.

        This method may be called at any time to refresh the state of the footer,
        so it should be a pure function.

        If this function returns ``None``, it will not cause anything to be
        rendered in the footer. You can use this to "hide" the footer based
        on state captured during the suite.
        """
        pass

    def after_test(self, test_index: int, test_result: TestResult) -> None:
        """
        This method is called after each test is executed,
        with the results of that test and the index of that test in the suite.

        Some ways you can use this method:
         - Capture state for use in other methods of your widget.
         - Print to the terminal using the attached Console (``self.console``).
           Anything printed this way will appear above the footer
           and will persist after the suite is done.
        """
        pass

    def after_suite(self, test_results: List[TestResult]) -> None:
        """
        This method is called after the suite is done executing
        (or is cancelled, or aborts mid-run, etc.),
        with results for all of the tests that have been run.

        Some ways you can use this method:
         - Change the return value of your footer to None to prevent it
           from appearing in the final persistent output.
        """
        pass


class TestPerLine(TestResultDisplayWidget):
    def after_test(self, test_index: int, test_result: TestResult) -> None:
        self.console.print(
            get_test_result_line(
                test_result, test_index, self.num_tests, self.progress_styles
            )
        )


class DotsDisplayWidget(TestResultDisplayWidget, abc.ABC):
    def __init__(self, num_tests: int, progress_styles: List[TestProgressStyle]):
        super().__init__(num_tests, progress_styles)

        self.base_max_dots_per_line = get_terminal_size().width
        if TestProgressStyle.INLINE in progress_styles:
            self.base_max_dots_per_line -= INLINE_PROGRESS_LEN

        self.dots_on_line = 0
        self.footer_text = self.get_blank_footer_text()

    def footer(self, test_results: List[TestResult]) -> Optional[RenderableType]:
        return self.footer_text

    def get_blank_footer_text(self) -> Text:
        return Text("", end="")

    @property
    @abc.abstractmethod
    def max_dots_for_current_line(self) -> int:
        raise NotImplementedError()

    def end_of_line(self, test_index):
        self.footer_text.append(self.get_end_of_line_for_dots(test_index=test_index))
        self.console.print(self.footer_text, end="")

        self.dots_on_line = 0
        self.footer_text = self.get_blank_footer_text()

    def get_end_of_line_for_dots(
        self,
        test_index: int,
    ) -> Text:
        if TestProgressStyle.INLINE in self.progress_styles and self.num_tests > 0:
            fill = (
                self.max_dots_for_current_line - self.dots_on_line + INLINE_PROGRESS_LEN
            )
            return Text(
                f"{(test_index + 1) / self.num_tests:>{fill}.0%}\n",
                style="muted",
            )
        else:
            return Text("\n")

    def after_suite(self, test_results: List[TestResult]) -> None:
        self.end_of_line(test_index=len(test_results) - 1)


class DotsGlobal(DotsDisplayWidget):
    @property
    def max_dots_for_current_line(self) -> int:
        return self.base_max_dots_per_line

    def after_test(self, test_index: int, test_result: TestResult) -> None:
        self.footer_text.append(get_dot(test_result))

        self.dots_on_line += 1
        if self.dots_on_line == self.max_dots_for_current_line:
            self.end_of_line(test_index)


class DotsPerModule(DotsDisplayWidget):
    def __init__(self, num_tests: int, progress_styles: List[TestProgressStyle]):
        super().__init__(num_tests, progress_styles)

        self.current_path = Path("")
        self.cwd = Path.cwd()

        self._max_dots_for_current_line = self.base_max_dots_per_line

    @property
    def max_dots_for_current_line(self) -> int:
        return self._max_dots_for_current_line

    def after_test(self, test_index: int, test_result: TestResult) -> None:
        # if we are starting a new module
        if test_result.test.path != self.current_path:
            # if this isn't the first module, add the end-of-line for the previous module
            if test_index > 0:
                self.end_of_line(test_index)

            self.current_path = test_result.test.path
            rel_path = str(self.current_path.relative_to(self.cwd))

            final_slash_idx = rel_path.rfind("/")
            if final_slash_idx != -1:
                path_text = Text("", end="").join(
                    [
                        Text(rel_path[: final_slash_idx + 1], style="muted"),
                        Text(rel_path[final_slash_idx + 1 :]),
                        Text(": "),
                    ]
                )
            else:
                path_text = Text(f"{rel_path}: ", end="")

            self.footer_text.append(path_text)

            self._max_dots_for_current_line = (
                self.base_max_dots_per_line - path_text.cell_len
            )

        if self.dots_on_line == self.max_dots_for_current_line:
            self.end_of_line(test_index)

            # we are now on a blank line with no path prefix
            self._max_dots_for_current_line = self.base_max_dots_per_line

        self.footer_text.append(get_dot(test_result))
        self.dots_on_line += 1


GREEN_CHECK = Text("✔", style="pass.textonly")
RED_X = Text("✘", style="fail.textonly")


class LiveTestBar(TestResultDisplayWidget):
    def __init__(self, num_tests: int, progress_styles: List[TestProgressStyle]):
        super().__init__(num_tests, progress_styles)

        self.spinner_column = SpinnerColumn(
            style="pass.textonly",
            finished_text=GREEN_CHECK,
        )
        self.test_description_column = RenderableColumn(Text(""))

        self.progress = Progress(
            self.spinner_column,
            self.test_description_column,
            console=rich_console,
        )

        self.task = self.progress.add_task("", total=num_tests)

    def footer(self, test_results: List[TestResult]) -> Optional[RenderableType]:
        return self.progress

    def after_test(self, test_index: int, test_result: TestResult) -> None:
        self.progress.update(self.task, advance=1)
        self.test_description_column.renderable = get_test_result_line(
            test_result=test_result,
            test_index=test_index,
            num_tests=self.num_tests,
            progress_styles=self.progress_styles,
        )

        if test_result.outcome.will_fail_session:
            self.console.print(
                get_test_result_line(
                    test_result=test_result,
                    test_index=test_index,
                    num_tests=self.num_tests,
                    progress_styles=self.progress_styles,
                    extra_left_pad=2,  # account for the spinner
                )
            )

            self.spinner_column.finished_text = RED_X
            self.spinner_column.spinner.style = "fail.textonly"


class SuiteProgressBar(TestResultDisplayWidget):
    def __init__(self, num_tests: int, progress_styles: List[TestProgressStyle]):
        super().__init__(num_tests, progress_styles)

        self.spinner_column = SpinnerColumn(
            style="pass.textonly",
            finished_text=GREEN_CHECK,
        )
        self.bar_column = BarColumn(
            complete_style="pass.textonly",
            finished_style="pass.textonly",
        )

        self.progress = Progress(
            self.spinner_column,
            TimeElapsedColumn(),
            self.bar_column,
            "[progress.percentage]{task.percentage:>3.0f}%",
            "[progress.percentage][{task.completed} / {task.total}]",
            console=self.console,
        )

        self.task = self.progress.add_task("Testing...", total=num_tests)

    def footer(self, test_results: List[TestResult]) -> Optional[RenderableType]:
        return self.progress

    def after_test(self, test_index: int, test_result: TestResult) -> None:
        self.progress.update(self.task, advance=1)

        if test_result.outcome.will_fail_session:
            self.spinner_column.finished_text = RED_X
            self.spinner_column.spinner.style = "fail.textonly"
            self.bar_column.complete_style = "fail.textonly"
            self.bar_column.finished_style = "fail.textonly"

    def after_suite(self, test_results: List[TestResult]) -> None:
        self.progress = None


class TerminalResultsWriter:
    def __init__(
        self,
        console: Console,
        num_tests: int,
        progress_styles: List[TestProgressStyle],
        widget_types: Iterable[Type[TestResultDisplayWidget]],
    ):
        self.console = console
        self.widgets = [
            widgets(num_tests=num_tests, progress_styles=progress_styles)
            for widgets in widget_types
        ]
        self.live = Live(
            console=console,
            renderable=self.footer(results=[]),
        )

    def footer(self, results: List[TestResult]) -> RenderableType:
        table = Table.grid()
        table.add_column()
        for f in filter(
            None, (component.footer(results) for component in self.widgets)
        ):
            table.add_row(f)

        return table

    def run(
        self,
        test_results: Iterator[TestResult],
        fail_limit: Optional[int],
    ) -> Tuple[List[TestResult], bool]:
        """
        Execute the test suite, returning the list of test results
        and a boolean that is true if the run was cancelled and false otherwise.
        """
        num_failures = 0
        results = []
        was_cancelled = False

        self.console.print()
        with self.live as live:
            try:
                for idx, result in enumerate(test_results):
                    # We need to re-enable the Live here in case
                    # it was disabled by the breakpoint debugger hook.
                    live.start(refresh=True)

                    for component in self.widgets:
                        component.after_test(idx, result)

                    live.update(self.footer(results))

                    results.append(result)

                    if result.outcome is TestOutcome.FAIL:
                        num_failures += 1

                    if num_failures == fail_limit:
                        break
            except KeyboardInterrupt:
                was_cancelled = True
            finally:
                for component in self.widgets:
                    component.after_suite(results)

                live.update(self.footer(results), refresh=True)

                return results, was_cancelled


class TestResultWriterBase:
    runtime_output_strategies = {
        TestOutputStyle.TEST_PER_LINE: TestPerLine,
        TestOutputStyle.DOTS_GLOBAL: DotsGlobal,
        TestOutputStyle.DOTS_MODULE: DotsPerModule,
        TestOutputStyle.LIVE: LiveTestBar,
        TestOutputStyle.NONE: TestResultDisplayWidget,
    }

    def __init__(
        self,
        console: Console,
        suite: Suite,
        test_output_style: TestOutputStyle,
        progress_styles: List[TestProgressStyle],
        config_path: Optional[Path],
        show_diff_symbols: bool = False,
    ):
        self.console = console
        self.suite = suite
        self.test_output_style = test_output_style
        self.progress_styles = progress_styles
        self.config_path = config_path
        self.show_diff_symbols = show_diff_symbols
        self.terminal_size = get_terminal_size()

    def output_all_test_results(
        self,
        test_results_gen: Generator[TestResult, None, None],
        fail_limit: Optional[int] = None,
    ) -> List[TestResult]:
        if not self.suite.num_tests:
            return []

        widget_types = [self.runtime_output_strategies[self.test_output_style]]
        if TestProgressStyle.BAR in self.progress_styles:
            widget_types.append(SuiteProgressBar)

        all_results, was_cancelled = TerminalResultsWriter(
            console=self.console,
            num_tests=self.suite.num_tests_with_parameterisation,
            progress_styles=self.progress_styles,
            widget_types=widget_types,
        ).run(test_results_gen, fail_limit)

        if was_cancelled:
            self.console.print(
                "Run cancelled - results for tests that ran shown below.",
                style="info",
            )

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
            self.console.print()

        return all_results

    @staticmethod
    def print_divider() -> None:
        rich_console.print(Rule(style="muted"))

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


class TestResultWriter(TestResultWriterBase):
    def output_why_test_failed_header(self, test_result: TestResult):
        test = test_result.test
        self.console.print(
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
            if err.operator in Comparison:
                self.console.print(self.get_source(err, test_result))
                self.console.print(self.get_pretty_comparison_failure(err))
        else:
            self.print_traceback(err)

    def get_source(self, err: TestFailure, test_result: TestResult) -> RenderableType:
        src_lines, line_num = inspect.getsourcelines(test_result.test.fn)
        src = Syntax(
            "".join(src_lines),
            "python",
            start_line=line_num,
            line_numbers=True,
            highlight_lines={err.error_line},
            background_color="default",
            theme="ansi_dark",
        )

        return Padding(src, (1, 0, 1, 4))

    def get_pretty_comparison_failure(self, err: TestFailure) -> RenderableType:
        if err.operator is Comparison.Equals:
            return self.get_pretty_failure_for_equals(err)
        elif err.operator in {Comparison.In, Comparison.NotIn}:
            return self.get_pretty_failure_for_in(err)
        else:
            return Text("", end="")

    def get_pretty_failure_for_equals(self, err: TestFailure) -> RenderableType:
        diff_msg = Text.assemble(
            ("LHS ", "pass.textonly"),
            ("vs ", "default"),
            ("RHS ", "fail.textonly"),
            ("shown below", "default"),
        )

        diff = Diff(
            err.lhs,
            err.rhs,
            width=self.terminal_size.width - 24,
            show_symbols=self.show_diff_symbols,
        )

        return RenderGroup(
            Padding(diff_msg, pad=(0, 0, 1, 2)),
            Padding(diff, pad=(0, 0, 1, 4)),
        )

    def get_pretty_failure_for_in(self, err: TestFailure) -> RenderableType:
        lhs_msg = Text.assemble(
            ("The ", "default"),
            ("item ", "pass.textonly"),
            *self.of_type(err.lhs),
        )
        lhs = Panel(
            Pretty(err.lhs),
            title=lhs_msg,
            title_align="left",
            border_style="pass.textonly",
            padding=1,
        )

        rhs_msg = Text.assemble(
            ("was not " if err.operator is Comparison.In else "was ", "bold default"),
            ("found in the ", "default"),
            ("container ", "fail.textonly"),
            *self.of_type(err.rhs),
        )
        rhs = Panel(
            Pretty(err.rhs),
            title=rhs_msg,
            title_align="left",
            border_style="fail.textonly",
            padding=1,
        )

        return Padding(RenderGroup(lhs, rhs), pad=(0, 0, 1, 2))

    def of_type(self, obj: object) -> Iterator[Tuple[str, str]]:
        yield "(of type ", "default"
        yield type(obj).__name__, "bold default"
        yield ")", "default"

    def print_traceback(self, err):
        trace = getattr(err, "__traceback__", "")
        if trace:
            # The first frame contains library internal code which is not
            # relevant to end users, so skip over it.
            trace = trace.tb_next
            tb = Traceback.from_exception(err.__class__, err, trace, show_locals=True)
            self.console.print(Padding(tb, pad=(0, 4, 1, 4)))
        else:
            self.console.print(str(err))

    def output_test_result_summary(
        self, test_results: List[TestResult], time_taken: float, show_slowest: int
    ):
        if show_slowest:
            self.console.print(TestTimingStatsPanel(test_results, show_slowest))

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
        self.console.print(result_summary_panel)

        self.console.print(
            Rule(
                f"[b]{exit_code.clean_name}[/b] in [b]{time_taken:.2f}[/b] seconds",
                style=result_style,
            )
        )

    def output_captured_stderr(self, test_result: TestResult):
        if test_result.captured_stderr:
            captured_stderr_lines = test_result.captured_stderr.split("\n")
            self.console.print(Padding(Text("Captured stderr"), pad=(0, 0, 1, 2)))
            for line in captured_stderr_lines:
                self.console.print(Padding(line, pad=(0, 0, 0, 4)))
            self.console.print()

    def output_captured_stdout(self, test_result: TestResult):
        if test_result.captured_stdout:
            captured_stdout_lines = test_result.captured_stdout.split("\n")
            self.console.print(Padding(Text("Captured stdout"), pad=(0, 0, 1, 2)))
            for line in captured_stdout_lines:
                self.console.print(Padding(line, pad=(0, 0, 0, 4)))
            self.console.print()

    def output_test_failed_location(self, test_result: TestResult):
        if isinstance(test_result.error, TestFailure) or isinstance(
            test_result.error, AssertionError
        ):
            self.console.print(
                Padding(
                    Text(
                        f"Failed at {os.path.relpath(test_result.test.path, Path.cwd())}:{test_result.error.error_line}"
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
        rich_console.print(Rule(Text(module, style="title")))

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
            rich_console.print(fixture_tree)


def make_fixture_information_tree(
    fixture: Fixture,
    used_by_tests: Collection[Test],
    fixtures_to_children: FixtureHierarchyMapping,
    fixtures_to_parents: FixtureHierarchyMapping,
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
            root.add("[usedby]used by [fail]no tests or fixtures")

    return root


def add_fixture_dependencies_to_tree(
    parent: Tree,
    fixture: Fixture,
    fixtures_to_parents_or_children: FixtureHierarchyMapping,
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
