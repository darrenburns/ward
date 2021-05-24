from unittest import mock

from pathlib import Path

from rich.rule import Rule
from rich.text import Text

from tests.utilities import example_test
from ward import using, fixture
from ward._terminal import outcome_to_colour, get_exit_code, SessionPrelude
from ward.models import ExitCode
from ward.testing import TestOutcome, each, test, TestResult


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


@test("outcome_to_colour({outcome}) returns '{colour}'")
def _(
    outcome=each(
        TestOutcome.PASS,
        TestOutcome.SKIP,
        TestOutcome.FAIL,
        TestOutcome.XFAIL,
        TestOutcome.XPASS,
        TestOutcome.DRYRUN,
    ),
    colour=each("green", "blue", "red", "magenta", "yellow", "green"),
):
    assert outcome_to_colour(outcome) == colour


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
    assert vars(next(render_iter)) == vars(Rule(
        Text(f"Ward 1.0.0dev1 | CPython 4.2", style="title",)
    ))
    assert next(render_iter) == (
        f"Found [b]123[/b] tests "
        f"and [b]456[/b] fixtures "
        f"in [b]1.23[/b] seconds."
    )


@test("SessionPrelude displays config path when it is supplied")
def _(prelude: SessionPrelude = prelude):
    prelude.config_path = Path("/path/to/pyproject.toml")
    render_iter = prelude.__rich_console__(None, None)
    next(render_iter)
    assert next(render_iter) == "Loaded config from [b]pyproject.toml[/b]."

