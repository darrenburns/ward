from pathlib import Path

from rich.console import RenderGroup
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from tests.utilities import example_test, print_to_string
from ward import fixture, using
from ward._terminal import (
    SessionPrelude,
    TestProgressStyle,
    TestTimingStatsPanel,
    get_exit_code,
    get_test_result_line,
    outcome_to_style,
)
from ward._testing import _Timer
from ward.models import ExitCode
from ward.testing import Test, TestOutcome, TestResult, test


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
    render_iter = prelude.__rich_console__(None, None)
    assert vars(next(render_iter)) == vars(
        Rule(Text("Ward 1.0.0dev1 | CPython 4.2", style="title"))
    )
    assert next(render_iter) == (
        "Found [b]123[/b] tests " "and [b]456[/b] fixtures " "in [b]1.23[/b] seconds."
    )


@test("SessionPrelude displays config path when it is supplied")
def _(prelude: SessionPrelude = prelude):
    prelude.config_path = Path("/path/to/pyproject.toml")
    render_iter = prelude.__rich_console__(None, None)
    next(render_iter)
    assert next(render_iter) == "Loaded config from [b]pyproject.toml[/b]."


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
        RenderGroup(
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

    render_group: RenderGroup = panel.renderable
    padding: Padding = render_group.renderables[0]
    assert padding.renderable == expected_panel.renderable.renderables[0].renderable


@test("TestTimingStatsPanel displays correct table listing slowest tests")
def _(timing_stats_panel=timing_stats_panel):
    panel: Panel = next(timing_stats_panel.__rich_console__(None, None))

    render_group: RenderGroup = panel.renderable
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
    return TestResult(
        test=Test(
            timer=_Timer(duration=4.0),
            fn=lambda: 1,
            description="test1",
            module_name="mod1",
        ),
        outcome=TestOutcome.FAIL,
    )


for idx, num_tests in [(0, 2)]:

    @test("get_test_result_line emits correct inline progress display")
    def _(idx=idx, num_tests=num_tests, test_result=test_result):
        output = print_to_string(
            get_test_result_line(
                test_result=test_result,
                idx=idx,
                num_tests=num_tests,
                progress_styles=[TestProgressStyle.INLINE],
            )
        )
        assert " 0%" in output
