import sys

import click
from blessings import Terminal

from ward.collect import get_info_for_modules, get_tests_in_modules, load_modules
from ward.fixtures import fixture_registry
from ward.suite import Suite
from ward.terminal import TestRunnerWriter, SimpleTestResultWrite, ExitCode
from ward.test_result import TestOutcome


@click.command()
@click.option(
    "-p", "--path", default=".", type=click.Path(exists=True), help="Path to tests."
)
@click.option(
    "-f", "--filter", help="Only run tests whose names contain the filter argument as a substring."
)
@click.option(
    "--hide-progress", is_flag=True, help="Show the progress bar"
)
def run(path, filter, hide_progress):
    term = Terminal()

    mod_infos = get_info_for_modules(path)
    modules = list(load_modules(mod_infos))
    tests = list(get_tests_in_modules(modules, filter=filter))

    suite = Suite(tests=tests, fixture_registry=fixture_registry)

    test_results = suite.generate_test_runs()

    if hide_progress:
        # TODO: Use same interface for outputting test results whether progress bar is shown or not
        results = SimpleTestResultWrite(terminal=term, suite=suite).output_all_test_results(test_results)
        if any(r.outcome == TestOutcome.FAIL for r in results):
            exit_code = ExitCode.TEST_FAILED
        else:
            exit_code = ExitCode.SUCCESS
    else:
        exit_code = TestRunnerWriter(
            suite=suite, terminal=term, test_results=test_results
        ).run_and_write_test_results()

    sys.exit(exit_code.value)
