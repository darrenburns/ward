from pathlib import Path
from typing import Optional, Tuple, Union

import click
import sys
from colorama import init

from ward._ward_version import __version__
from ward.config import read_config_toml
from ward.core import run_tests_at_path_and_output_results
from ward.terminal import get_exit_code
from ward.util import find_project_root
from ward.watch import enter_watch_mode

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
    config_paths = config.get("path", ".")
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
@click.option(
    "--capture-output/--no-capture-output",
    default=True,
    help="Enable or disable output capturing.",
)
# TODO: Should this be a flag, and we should use --path to get
#  the paths to watch?
@click.option(
    "--watch",
    type=click.Path(),
    multiple=False,
    callback=enter_watch_mode,
    help="Enter interactive mode, watching a directory for changes.",
    is_eager=True,
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
    capture_output: bool,
    watch: str,
    config: str,
):
    results = run_tests_at_path_and_output_results(
        path, test_output_style, search, capture_output, fail_limit, order
    )
    exit_code = get_exit_code(results)
    sys.exit(exit_code.value)
