import sys

import click
from blessings import Terminal

from ward.collect import get_info_for_modules, get_tests_in_modules, load_modules
from ward.fixtures import fixture_registry
from ward.suite import Suite
from ward.terminal import TestResultWriter


@click.command()
@click.option(
    "-p", "--path", default=".", type=click.Path(exists=True), help="Path to tests."
)
@click.option(
    "-f", "--filter", help="Only run tests whose names contain the filter argument as a substring."
)
def run(path, filter):
    term = Terminal()

    mod_infos = get_info_for_modules(path)
    modules = list(load_modules(mod_infos))
    tests = list(get_tests_in_modules(modules, filter=filter))

    suite = Suite(tests=tests, fixture_registry=fixture_registry)

    test_results = suite.generate_test_runs()

    exit_code = TestResultWriter(
        suite=suite, terminal=term, test_results=test_results
    ).write_test_results_to_terminal()

    sys.exit(exit_code.value)
