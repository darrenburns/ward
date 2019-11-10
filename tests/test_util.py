from tests.test_suite import example_test
from ward import expect, test, using, fixture
from ward.testing import TestOutcome, TestResult, each
from ward.util import ExitCode, get_exit_code, truncate


@test(
    "get_exit_code returns ExitCode.SUCCESS when PASS, SKIP and XFAIL in test results"
)
@using(
    example=example_test,
)
def _(example=example_test):
    test_results = [
        TestResult(test=example, outcome=TestOutcome.PASS),
        TestResult(test=example, outcome=TestOutcome.SKIP),
        TestResult(test=example, outcome=TestOutcome.XFAIL),
    ]
    exit_code = get_exit_code(test_results)

    expect(exit_code).equals(ExitCode.SUCCESS)


@test("get_exit_code returns ExitCode.SUCCESS when no test results")
def _():
    exit_code = get_exit_code([])

    expect(exit_code).equals(ExitCode.SUCCESS)


@test("get_exit_code returns ExitCode.FAILED when XPASS in test results")
def _(example=example_test):
    test_results = [
        TestResult(test=example, outcome=TestOutcome.XPASS),
        TestResult(test=example, outcome=TestOutcome.PASS),
    ]
    exit_code = get_exit_code(test_results)

    expect(exit_code).equals(ExitCode.FAILED)


@fixture
def s():
    return "hello world"


@test("truncate('{input}', num_chars={num_chars}) returns '{expected}'")
def _(
    input=s,
    num_chars=each(20, 11, 10, 5),
    expected=each(s, s, "hello w...", "he..."),
):
    result = truncate(input, num_chars)
    expect(result).equals(expected)
