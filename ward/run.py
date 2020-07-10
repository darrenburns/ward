import sys
from pathlib import Path
from timeit import default_timer
from typing import Optional, Tuple

import click
from click_default_group import DefaultGroup
from colorama import init
from cucumber_tag_expressions import parse as parse_tags
from cucumber_tag_expressions.model import Expression

from ward._ward_version import __version__
from ward.collect import (
    get_info_for_modules,
    get_tests_in_modules,
    load_modules,
    filter_tests,
    filter_fixtures,
)
from ward.config import set_defaults_from_config
from ward.rewrite import rewrite_assertions_in_tests
from ward.suite import Suite
from ward.fixtures import _DEFINED_FIXTURES
from ward.terminal import SimpleTestResultWrite, output_fixtures, get_exit_code

init()

sys.path.append(".")


# TODO: simplify to use invoke_without_command and ctx.forward once https://github.com/pallets/click/issues/430 is resolved
@click.group(
    context_settings={"max_content_width": 100},
    cls=DefaultGroup,
    default="test",
    default_if_no_args=True,
)
@click.pass_context
def run(ctx: click.Context):
    pass


config = click.option(
    "--config",
    type=click.Path(
        exists=False, file_okay=True, dir_okay=False, readable=True, allow_dash=False
    ),
    callback=set_defaults_from_config,
    help="Read configuration from PATH.",
    is_eager=True,
)
path = click.option(
    "-p",
    "--path",
    type=click.Path(exists=True),
    multiple=True,
    is_eager=True,
    help="Look for tests in PATH.",
)
exclude = click.option(
    "--exclude",
    type=click.STRING,
    multiple=True,
    help="Paths to ignore while searching for tests. Accepts glob patterns.",
)


@run.command()
@config
@path
@exclude
@click.option(
    "--search",
    help="Search test names, bodies, descriptions and module names for the search query and only keep matching tests.",
)
@click.option(
    "--tags",
    help="Find tests matching a tag expression (e.g. 'unit and not slow').",
    metavar="EXPR",
    type=parse_tags,
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
    "--show-diff-symbols/--hide-diff-symbols",
    default=False,
    help="If enabled, diffs will use symbols such as '?', '-', '+' and '^' instead of colours to highlight differences.",
)
@click.option(
    "--capture-output/--no-capture-output",
    default=True,
    help="Enable or disable output capturing.",
)
@click.option(
    "--show-slowest",
    type=int,
    help="Record and display duration of n longest running tests",
    default=0,
)
@click.option(
    "--dry-run/--no-dry-run",
    help="Print all tests without executing them",
    default=False,
)
@click.version_option(version=__version__)
@click.pass_context
def test(
    ctx: click.Context,
    config: str,
    config_path: Optional[Path],
    path: Tuple[str],
    exclude: Tuple[str],
    search: Optional[str],
    tags: Optional[Expression],
    fail_limit: Optional[int],
    test_output_style: str,
    order: str,
    capture_output: bool,
    show_slowest: int,
    show_diff_symbols: bool,
    dry_run: bool,
):
    """Run tests."""
    start_run = default_timer()
    paths = [Path(p) for p in path]
    mod_infos = get_info_for_modules(paths, exclude)
    modules = list(load_modules(mod_infos))
    unfiltered_tests = get_tests_in_modules(modules, capture_output)
    filtered_tests = list(filter_tests(unfiltered_tests, query=search, tag_expr=tags,))

    # Rewrite assertions in each test
    tests = rewrite_assertions_in_tests(filtered_tests)

    time_to_collect = default_timer() - start_run

    suite = Suite(tests=tests)
    test_results = suite.generate_test_runs(order=order, dry_run=dry_run)

    writer = SimpleTestResultWrite(
        suite=suite,
        test_output_style=test_output_style,
        config_path=config_path,
        show_diff_symbols=show_diff_symbols,
    )
    writer.output_header(time_to_collect=time_to_collect)
    results = writer.output_all_test_results(test_results, fail_limit=fail_limit)
    time_taken = default_timer() - start_run
    writer.output_test_result_summary(results, time_taken, show_slowest)

    exit_code = get_exit_code(results)

    sys.exit(exit_code.value)


@run.command()
@config
@path
@exclude
@click.option(
    "-f",
    "--fixture-path",
    help="Only display fixtures defined in or below the given paths.",
    multiple=True,
    type=Path,
)
@click.option(
    "--search",
    help="Search fixtures names, bodies, and module names for the search query and only keep matching fixtures.",
)
@click.option(
    "--show-scopes/--no-show-scopes",
    help="Display each fixture's scope.",
    default=True,
)
@click.option(
    "--show-docstrings/--no-show-docstrings",
    help="Display each fixture's docstring.",
    default=False,
)
@click.option(
    "--show-dependencies/--no-show-dependencies",
    help="Display the fixtures and tests that each fixture depends on and is used by. Only displays direct dependencies; use --show-dependency-trees to show all dependency information.",
    default=False,
)
@click.option(
    "--show-dependency-trees/--no-show-dependency-trees",
    help="Display the entire dependency tree for each fixture.",
    default=False,
)
@click.option(
    "--full/--no-full",
    help="Display all available information on each fixture.",
    default=False,
)
@click.pass_context
def fixtures(
    ctx: click.Context,
    config: str,
    config_path: Optional[Path],
    path: Tuple[str],
    exclude: Tuple[str],
    fixture_path: Tuple[Path],
    search: Optional[str],
    show_scopes: bool,
    show_docstrings: bool,
    show_dependencies: bool,
    show_dependency_trees: bool,
    full: bool,
):
    """Show information on fixtures."""
    paths = [Path(p) for p in path]
    mod_infos = get_info_for_modules(paths, exclude)
    modules = list(load_modules(mod_infos))
    tests = list(get_tests_in_modules(modules, capture_output=True))

    filtered_fixtures = list(
        filter_fixtures(_DEFINED_FIXTURES, query=search, paths=fixture_path)
    )

    output_fixtures(
        fixtures=filtered_fixtures,
        tests=tests,
        show_scopes=show_scopes or full,
        show_docstrings=show_docstrings or full,
        show_dependencies=show_dependencies or full,
        show_dependency_trees=show_dependency_trees or full,
    )
