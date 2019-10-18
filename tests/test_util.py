from ward import expect
from ward.test_result import TestResult, TestOutcome
from ward.util import get_exit_code, ExitCode


def test_get_exit_code_returns_success_when_skip_and_pass_and_xfail_present(example_test):
    test_results = [
        TestResult(test=example_test, outcome=TestOutcome.PASS),
        TestResult(test=example_test, outcome=TestOutcome.SKIP),
        TestResult(test=example_test, outcome=TestOutcome.XFAIL),
    ]
    exit_code = get_exit_code(test_results)

    expect(exit_code).equals(ExitCode.SUCCESS)


def test_get_exit_code_returns_success_when_no_test_results():
    exit_code = get_exit_code([])

    expect(exit_code).equals(ExitCode.SUCCESS)


def test_get_exit_code_returns_fail_when_xpass_present(example_test):
    test_results = [
        TestResult(test=example_test, outcome=TestOutcome.XPASS),
        TestResult(test=example_test, outcome=TestOutcome.PASS),
    ]
    exit_code = get_exit_code(test_results)

    expect(exit_code).equals(ExitCode.FAILED)
