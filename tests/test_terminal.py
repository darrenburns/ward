from tests.utilities import example_test
from ward import using
from ward.terminal import outcome_to_colour, get_exit_code, ExitCode
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
    ),
    colour=each("green", "blue", "red", "magenta", "yellow"),
):
    assert outcome_to_colour(outcome) == colour
