import sys
from pathlib import Path
from timeit import default_timer
from typing import Optional, Tuple, Union

import click
from colorama import init

from ward._ward_version import __version__
from ward.collect import (
    get_info_for_modules,
    get_tests_in_modules,
    load_modules,
    search_generally,
)
from ward.config import read_config_toml
from ward.suite import Suite
from ward.terminal import SimpleTestResultWrite
from ward.util import get_exit_code, find_project_root

init()

sys.path.append(".")

CONFIG_FILE = "pyproject.toml"


def set_defaults_from_config(
    context: click.Context, param: click.Parameter, value: Union[str, int],
) -> Path:
    supplied_paths = context.params.get("path")

    search_paths = supplied_paths
    if not search_paths:
        search_paths = (".",)

    project_root = find_project_root([Path(path) for path in search_paths])
    config = read_config_toml(project_root, CONFIG_FILE)

    # Handle params where multiple=True
    config_paths = config.get("path")
    if not supplied_paths:
        if config_paths and isinstance(config_paths, list):
            config["path"] = config_paths
        else:
            config["path"] = [config_paths]

    if context.default_map is None:
        context.default_map = {}

    context.default_map.update(config)
    return project_root


@click.command()
@click.option(
    "--search",
    help="Search test names, bodies, descriptions and module names for the search query and only run matching tests.",
)
@click.option(
    "--fail-limit",
    type=int,
    help="The maximum number of failures that are allowed to occur in a run before it is automatically cancelled.",
)
@click.option(
    "--test-output-style",
    type=click.Choice(
        ["test-per-line", "dots-global", "dots-module"], case_sensitive=False,
    ),
    default="test-per-line",
)
@click.option(
    "--order",
    type=click.Choice(["standard", "random"], case_sensitive=False),
    default="standard",
    help="Specify the order in which tests should run.",
)
@click.version_option(version=__version__)
@click.option(
    "--config",
    type=click.Path(
        exists=False, file_okay=True, dir_okay=False, readable=True, allow_dash=False
    ),
    callback=set_defaults_from_config,
    help="Read configuration from PATH.",
    is_eager=True,
)
@click.option(
    "-p",
    "--path",
    type=click.Path(exists=True),
    multiple=True,
    is_eager=True,
    help="Look for tests in PATH.",
)
@click.pass_context
def run(
    ctx: click.Context,
    path: Tuple[str],
    search: Optional[str],
    fail_limit: Optional[int],
    test_output_style: str,
    order: str,
    config: str,
):
    start_run = default_timer()
    paths = [Path(p) for p in path]
    mod_infos = get_info_for_modules(paths)
    modules = list(load_modules(mod_infos))
    unfiltered_tests = get_tests_in_modules(modules)
    tests = list(search_generally(unfiltered_tests, query=search))
    time_to_collect = default_timer() - start_run

    suite = Suite(tests=tests)
    test_results = suite.generate_test_runs(order=order)

    writer = SimpleTestResultWrite(suite=suite, test_output_style=test_output_style)
    results = writer.output_all_test_results(
        test_results, time_to_collect=time_to_collect, fail_limit=fail_limit
    )
    time_taken = default_timer() - start_run
    writer.output_test_result_summary(results, time_taken)

    exit_code = get_exit_code(results)

    sys.exit(exit_code.value)
