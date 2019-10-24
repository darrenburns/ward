import os
import platform
import sys
from timeit import default_timer

import click
from colorama import init

from ward.collect import get_info_for_modules, get_tests_in_modules, load_modules, filter_generally
from ward.fixtures import fixture_registry
from ward.suite import Suite
from ward.terminal import SimpleTestResultWrite
from ward.util import get_exit_code

init()

if platform.system() == "Windows":
    os.system("color")


@click.command()
@click.option(
    "-p", "--path", default=".", type=click.Path(exists=True), help="Path to tests."
)
@click.option(
    "-f",
    "--filter",
    help="Search test names, descriptions and module names for the filter and only run matching tests.",
)
@click.option(
    "--fail-limit",
    type=int,
    help="The maximum number of failures that are allowed to occur in a run before it is automatically cancelled.",
)
def run(path, filter, fail_limit):
    start_run = default_timer()

    mod_infos = get_info_for_modules(path)
    modules = list(load_modules(mod_infos))
    unfiltered_tests = get_tests_in_modules(modules)
    tests = filter_generally(unfiltered_tests, filter=filter)
    time_to_collect = default_timer() - start_run

    suite = Suite(tests=list(tests), fixture_registry=fixture_registry)
    test_results = suite.generate_test_runs()

    writer = SimpleTestResultWrite(suite=suite)
    results = writer.output_all_test_results(
        test_results, time_to_collect=time_to_collect, fail_limit=fail_limit
    )
    time_taken = default_timer() - start_run
    writer.output_test_result_summary(results, time_taken)

    exit_code = get_exit_code(results)

    sys.exit(exit_code.value)
