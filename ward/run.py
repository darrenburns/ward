import sys
from pathlib import Path
from timeit import default_timer

import click
from colorama import init

from ward._ward_version import __version__
from ward.collect import (
    get_info_for_modules,
    get_tests_in_modules,
    load_modules,
    search_generally,
)
from ward.suite import Suite
from ward.terminal import SimpleTestResultWrite
from ward.util import get_exit_code

init()

sys.path.append(".")


@click.command()
@click.option(
    "-p",
    "--path",
    default=".",
    type=click.Path(exists=True),
    help="Path to tests.",
    multiple=True,
)
@click.option(
    "--search",
    help="Search test names, descriptions and module names for the search query and only run matching tests.",
)
@click.option(
    "--fail-limit",
    type=int,
    help="The maximum number of failures that are allowed to occur in a run before it is automatically cancelled.",
)
@click.option(
    "--test-output-style",
    type=click.Choice(
        ["test-per-line", "dots-global", "dots-module"], case_sensitive=False
    ),
)
@click.version_option(version=__version__)
def run(path, search, fail_limit, test_output_style):
    start_run = default_timer()

    paths = [Path(p) for p in path]
    mod_infos = get_info_for_modules(paths)
    modules = list(load_modules(mod_infos))
    unfiltered_tests = get_tests_in_modules(modules)
    tests = search_generally(unfiltered_tests, query=search)
    time_to_collect = default_timer() - start_run

    suite = Suite(tests=list(tests))
    test_results = suite.generate_test_runs()

    writer = SimpleTestResultWrite(suite=suite, test_output_style=test_output_style)
    results = writer.output_all_test_results(
        test_results, time_to_collect=time_to_collect, fail_limit=fail_limit
    )
    time_taken = default_timer() - start_run
    writer.output_test_result_summary(results, time_taken)

    exit_code = get_exit_code(results)

    sys.exit(exit_code.value)
