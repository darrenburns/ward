from pathlib import Path
from typing import Union
from unittest.mock import Mock

from rich.console import Console, Group
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from tests.utilities import example_test, testable_test
from ward import fixture, using
from ward._suite import Suite
from ward._terminal import (
    SessionPrelude,
    TestOutputStyle,
    TestProgressStyle,
    TestResultWriter,
    TestTimingStatsPanel,
    get_dot,
    get_exit_code,
    get_test_result_line,
    outcome_to_style,
)
from ward._testing import _Timer
from ward.expect import Comparison, TestAssertionFailure
from ward.models import ExitCode
from ward.testing import Test, TestOutcome, TestResult, test

expected_output: Union[str, Text]


@test(
    "get_exit_code returns ExitCode.SUCCESS when PASS, SKIP and XFAIL in test results"
)
@using(example=example_test)
def _(example):
    test_results = [
        TestResult(test=example, outcome=TestOutcome.PASS),
        TestResult(test=example, outcome=TestOutcome.SKIP),
        TestResult(test=example, outcome=TestOutcome.XFAIL),
    ]
    exit_code = get_exit_code(test_results)

    assert exit_code == ExitCode.SUCCESS


@test("get_exit_code returns ExitCode.SUCCESS when no test results")
def _():
    exit_code = get_exit_code([])

    assert exit_code == ExitCode.NO_TESTS_FOUND


@test("get_exit_code returns ExitCode.FAILED when XPASS in test results")
def _(example=example_test):
    test_results = [
        TestResult(test=example, outcome=TestOutcome.XPASS),
        TestResult(test=example, outcome=TestOutcome.PASS),
    ]
    exit_code = get_exit_code(test_results)

    assert exit_code == ExitCode.FAILED


for test_outcome, output_style in [
    (TestOutcome.PASS, "pass"),
    (TestOutcome.SKIP, "skip"),
    (TestOutcome.FAIL, "fail"),
    (TestOutcome.XFAIL, "xfail"),
    (TestOutcome.XPASS, "xpass"),
    (TestOutcome.DRYRUN, "dryrun"),
]:

    @test("outcome_to_style({outcome}) returns '{style}'")
    def _(outcome=test_outcome, style=output_style):
        assert outcome_to_style(outcome) == style


@fixture
def prelude():
    return SessionPrelude(
        time_to_collect_secs=1.23456,
        num_tests_collected=123,
        num_fixtures_collected=456,
        config_path=None,
        python_impl="CPython",
        python_version="4.2",
        ward_version="1.0.0dev1",
    )


@test("SessionPrelude displays correct info when no config supplied")
def _(prelude: SessionPrelude = prelude):
    render_iter = prelude.__rich_console__(None, None)  # type: ignore[arg-type]
    assert vars(next(render_iter)) == vars(  # type: ignore[call-overload]
        Rule(Text("Ward 1.0.0dev1 | CPython 4.2", style="title"))
    )
    assert next(render_iter) == (  # type: ignore[call-overload]
        "Found [b]123[/b] tests " "and [b]456[/b] fixtures " "in [b]1.23[/b] seconds."
    )


@test("SessionPrelude displays config path when it is supplied")
def _(prelude: SessionPrelude = prelude):
    prelude.config_path = Path("/path/to/pyproject.toml")
    render_iter = prelude.__rich_console__(None, None)  # type: ignore[arg-type]
    next(render_iter)  # type: ignore[call-overload]
    assert next(render_iter) == "Loaded config from [b]pyproject.toml[/b]."  # type: ignore[call-overload]


@fixture
def timing_stats_panel():
    return TestTimingStatsPanel(
        [
            TestResult(
                test=Test(
                    timer=_Timer(duration=4.0),
                    fn=lambda: 1,
                    description="test1",
                    module_name="mod1",
                ),
                outcome=TestOutcome.FAIL,
            ),
            TestResult(
                test=Test(
                    timer=_Timer(duration=3.0),
                    fn=lambda: 1,
                    description="test2",
                    module_name="mod2",
                ),
                outcome=TestOutcome.FAIL,
            ),
            TestResult(
                test=Test(
                    timer=_Timer(duration=5.0),
                    fn=lambda: 1,
                    description="test3",
                    module_name="mod3",
                ),
                outcome=TestOutcome.PASS,
            ),
        ],
        num_tests_to_show=3,
    )


@fixture
def timing_stats_expected_table():
    expected_table = Table.grid(padding=(0, 2, 0, 0))
    expected_table.add_column(justify="right")
    expected_table.add_column()
    expected_table.add_column()

    expected_table.add_row("[b]5000[/b]ms", Text("mod:123"), "test3")
    expected_table.add_row("[b]4000[/b]ms", Text("mod:123"), "test1")
    expected_table.add_row("[b]3000[/b]ms", Text("mod:123"), "test2")

    return expected_table


@fixture
def timing_stats_expected_panel(expected_table=timing_stats_expected_table):
    return Panel(
        Group(
            Padding(
                "Median: [b]4000.00[/b]ms"
                " [muted]|[/muted] "
                "99th Percentile: [b]5000.00[/b]ms",
                pad=(0, 0, 1, 0),
            ),
            expected_table,
        ),
        title="[b white]3 Slowest Tests[/b white]",
        style="none",
        border_style="rule.line",
    )


@test("TestTimingStatsPanel has correct header and styling")
def _(
    timing_stats_panel=timing_stats_panel, expected_panel=timing_stats_expected_panel
):
    panel = next(timing_stats_panel.__rich_console__(None, None))

    assert panel.title == expected_panel.title
    assert panel.border_style == expected_panel.border_style
    assert panel.style == expected_panel.style


@test("TestTimingStatsPanel displays correct summary stats")
def _(
    timing_stats_panel=timing_stats_panel, expected_panel=timing_stats_expected_panel
):
    panel: Panel = next(timing_stats_panel.__rich_console__(None, None))

    render_group: Group = panel.renderable
    padding: Padding = render_group.renderables[0]
    assert padding.renderable == expected_panel.renderable.renderables[0].renderable


@test("TestTimingStatsPanel displays correct table listing slowest tests")
def _(timing_stats_panel=timing_stats_panel):
    panel: Panel = next(timing_stats_panel.__rich_console__(None, None))

    render_group: Group = panel.renderable
    table: Table = render_group.renderables[1]

    assert len(table.rows) == 3
    expected_durations = [
        "[b]5000[/b]ms",
        "[b]4000[/b]ms",
        "[b]3000[/b]ms",
    ]
    expected_test_descriptions = ["test3", "test1", "test2"]
    assert table.columns[0]._cells == expected_durations
    assert len(table.columns[1]._cells) == 3
    assert table.columns[2]._cells == expected_test_descriptions


@fixture
def test_result() -> TestResult:
    @testable_test
    def _():
        assert True

    return TestResult(
        test=Test(
            timer=_Timer(duration=4.0),
            fn=_,
            description="test1",
            module_name="mod1",
        ),
        outcome=TestOutcome.FAIL,
    )


for idx, num_tests, expected_output in [
    (0, 2, " 50%"),
    (1, 2, "100%"),
    (1, 3, " 67%"),
    (2, 3, "100%"),
    (16, 17, "100%"),
]:

    @test(
        "get_test_result_line with inline progress for test {idx} with {num_tests} tests emits {expected_output!r}"
    )
    def _(
        idx=idx,
        num_tests=num_tests,
        expected_output=expected_output,
        test_result=test_result,
    ):
        output = get_test_result_line(
            test_result=test_result,
            test_index=idx,
            num_tests=num_tests,
            progress_styles=[TestProgressStyle.INLINE],
        )

        assert expected_output == list(output.columns[-1].cells)[0]


for outcome, expected_output in [
    (TestOutcome.PASS, Text(".", style="pass")),
    (TestOutcome.FAIL, Text("F", style="fail")),
    (TestOutcome.SKIP, Text("-", style="skip")),
    (TestOutcome.XPASS, Text("U", style="xpass")),
    (TestOutcome.XFAIL, Text("x", style="xfail")),
    (TestOutcome.DRYRUN, Text(".", style="dryrun")),
]:

    @test("get_dot emits {expected_output!r} for test outcome {outcome}")
    def _(outcome=outcome, expected_output=expected_output):
        assert expected_output == get_dot(
            TestResult(
                test=Test(
                    timer=_Timer(duration=4.0),
                    fn=lambda: 1,
                    description="test1",
                    module_name="mod1",
                ),
                outcome=outcome,
            )
        )


@fixture
def mock_rich_console():
    return Mock(spec=Console)


@fixture
def writer(console=mock_rich_console):
    yield TestResultWriter(
        console, Suite([]), TestOutputStyle.LIVE, [TestProgressStyle.INLINE], None
    )


for left, right in [
    ("abc", "abd"),
    (123, 124),
    ({"hello": "world"}, {"helo", "world"}),
    ({"a": "b"}, [1, 2, 3, 4]),
]:

    @test("TestResultWriter.get_diff handles assert `==` failure")
    def _(lhs=left, rhs=right, writer=writer, console=mock_rich_console):
        failure = TestAssertionFailure("fail", lhs, rhs, 1, Comparison.Equals, "test")
        diff_render = writer.get_diff(failure)

        # Don't check anything more than this. We just want to exercise this
        # code and ensure it doesn't error. The rendering of the diff itself
        # is tested in detail in test_diff.
        assert diff_render.title.plain == "Difference (LHS vs RHS)"


for left, right in [
    ("a", "bcdef"),
    (1, [2, 3, 4]),
    ("a", {"b": 1}),
]:

    @test("TestResultWriter.get_operands handles assert `in` failure")
    def _(lhs=left, rhs=right, writer=writer):
        failure = TestAssertionFailure("fail", lhs, rhs, 1, Comparison.In, "test")
        lhs_render, rhs_render = writer.get_operands(failure).renderables

        assert lhs_render.title.plain == f"The item (of type {type(lhs).__name__})"
        assert (
            rhs_render.title.plain
            == f"was not found in the container (of type {type(rhs).__name__})"
        )


for left, right in [
    ("a", "abc"),
    (1, [1, 2, 3, 4]),
    ("a", {"a": 1}),
]:

    @test("TestResultWriter.get_operands handles assert `not in` failure")
    def _(lhs=left, rhs=right, writer=writer):
        failure = TestAssertionFailure("fail", lhs, rhs, 1, Comparison.NotIn, "test")
        lhs_render, rhs_render = writer.get_operands(failure).renderables

        assert lhs_render.title.plain == f"The item (of type {type(lhs).__name__})"
        assert (
            rhs_render.title.plain
            == f"was found in the container (of type {type(rhs).__name__})"
        )


for comparison, description in [
    (Comparison.Equals, "not equal to"),
    (Comparison.NotEquals, "equal to"),
    (Comparison.LessThan, "less than"),
    (Comparison.LessThanEqualTo, "less than or equal to"),
    (Comparison.GreaterThan, "greater than"),
    (Comparison.GreaterThanEqualTo, "greater than or equal to"),
]:

    @test(
        "TestResultWriter.get_operands has a specialized description for `{comparison.value}`"
    )
    def _(writer=writer, comparison=comparison, description=description):
        failure = TestAssertionFailure("fail", "a", "b", 1, comparison, "test")
        lhs_render, rhs_render = writer.get_operands(failure).renderables

        assert description in rhs_render.title.plain


for comparison in Comparison:

    @test(
        "TestResultWriter.get_pretty_comparison_failure can handle `{comparison.value}` failures"
    )
    def _(comparison=comparison, writer=writer):
        failure = TestAssertionFailure("fail", "a", "b", 1, comparison, "")
        renderable = writer.get_pretty_comparison_failure(failure)

        assert renderable is not None


@test("TestResultWriter.output_all_test_results returns empty list if suite is empty")
def _(console=mock_rich_console):
    suite = Suite([])
    result_writer = TestResultWriter(
        console=console,
        suite=suite,
        test_output_style=TestOutputStyle.TEST_PER_LINE,
        progress_styles=[TestProgressStyle.INLINE],
        config_path=None,
    )

    result = result_writer.output_all_test_results(_ for _ in ())
    assert result == []
    assert not console.print.called
