from ward import expect, test
from ward.test_result import TestResult, TestOutcome
from ward.util import get_exit_code, ExitCode


@test(
    "get_exit_code returns ExitCode.SUCCESS when PASS, SKIP and XFAIL in test results"
)
def _(example_test):
    test_results = [
        TestResult(test=example_test, outcome=TestOutcome.PASS),
        TestResult(test=example_test, outcome=TestOutcome.SKIP),
        TestResult(test=example_test, outcome=TestOutcome.XFAIL),
    ]
    exit_code = get_exit_code(test_results)

    expect(exit_code).equals(ExitCode.SUCCESS)


@test("get_exit_code returns ExitCode.SUCCESS when no test results")
def _():
    exit_code = get_exit_code([])

    expect(exit_code).equals(ExitCode.SUCCESS)


@test("get_exit_code returns ExitCode.FAILED when XPASS in test results")
def _(example_test):
    test_results = [
        TestResult(test=example_test, outcome=TestOutcome.XPASS),
        TestResult(test=example_test, outcome=TestOutcome.PASS),
    ]
    exit_code = get_exit_code(test_results)

    expect(exit_code).equals(ExitCode.FAILED)
