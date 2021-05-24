import pdb
import sys
from pathlib import Path
from random import shuffle
from timeit import default_timer
from typing import Optional, Tuple, List

import click
import click_completion
import colorama
from click_default_group import DefaultGroup
from cucumber_tag_expressions import parse as parse_tags
from cucumber_tag_expressions.model import Expression
from rich.console import ConsoleRenderable

from ward._collect import (
    get_info_for_modules,
    get_tests_in_modules,
    load_modules,
    filter_tests,
    filter_fixtures,
)
from ward._config import set_defaults_from_config
from ward._debug import init_breakpointhooks
from ward._rewrite import rewrite_assertions_in_tests
from ward._suite import Suite
from ward._terminal import (
    SimpleTestResultWrite,
    output_fixtures,
    get_exit_code,
    TestProgressStyle,
    TestOutputStyle,
    console,
    SessionPrelude,
)
from ward._ward_version import __version__
from ward.config import Config
from ward.fixtures import _DEFINED_FIXTURES
from ward.hooks import plugins, register_hooks_in_modules

colorama.init()
click_completion.init()

sys.path.append(".")


def _register_hooks(context: click.Context, param: click.Parameter, hook_module_names):
    register_hooks_in_modules(plugin_manager=plugins, module_names=hook_module_names)


# TODO: simplify to use invoke_without_command and ctx.forward once
#  https://github.com/pallets/click/issues/430 is resolved
@click.group(
    context_settings={"max_content_width": 100},
    cls=DefaultGroup,
    default="test",
    default_if_no_args=True,
)
@click.pass_context
def run(ctx: click.Context):
    pass


config_option = click.option(
    "--config",
    type=click.Path(
        exists=False, file_okay=True, dir_okay=False, readable=True, allow_dash=False
    ),
    callback=set_defaults_from_config,
    help="Read configuration from PATH.",
    is_eager=True,
)
path_option = click.option(
    "-p",
    "--path",
    type=click.Path(exists=True),
    multiple=True,
    is_eager=True,
    help="Look for tests in PATH.",
)
exclude_option = click.option(
    "--exclude",
    type=click.STRING,
    multiple=True,
    help="Paths to ignore while searching for tests. Accepts glob patterns.",
)
hook_module = click.option(
    "--hook-module",
    type=click.STRING,
    callback=_register_hooks,
    multiple=True,
    help="Modules to search for hook implementations in.",
)


@run.command()
@config_option
@path_option
@exclude_option
@hook_module
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
    type=click.Choice(list(TestOutputStyle), case_sensitive=False),
    default="test-per-line",
    help="The style of output for displaying individual test results during the run.",
)
@click.option(
    "--progress-style",
    type=click.Choice(list(TestProgressStyle), case_sensitive=False),
    multiple=True,
    default=["inline"],
    help=f"""\
    The style of progress indicator to use during the run.
    Pass multiple times to enable multiple styles.
    The '{TestProgressStyle.BAR}' style is not compatible with the '{TestOutputStyle.DOTS_GLOBAL}' and '{TestOutputStyle.DOTS_MODULE}' test output styles.
    """,
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
    progress_style: List[str],
    order: str,
    capture_output: bool,
    show_slowest: int,
    show_diff_symbols: bool,
    dry_run: bool,
    hook_module: Tuple[str],
):
    """Run tests."""
    config_params = ctx.params.copy()
    config_params.pop("config")

    config = Config(**config_params, plugin_config=config_params.get("plugins", {}))
    progress_styles = [TestProgressStyle(ps) for ps in progress_style]

    if TestProgressStyle.BAR in progress_styles and test_output_style in {
        "dots-global",
        "dots-module",
    }:
        raise click.BadOptionUsage(
            "progress_style",
            f"The '{TestProgressStyle.BAR}' progress style cannot be used with dots-based test output styles (you asked for '{test_output_style}').",
        )

    init_breakpointhooks(pdb, sys)
    start_run = default_timer()

    print_before: Tuple[ConsoleRenderable] = plugins.hook.before_session(config=config)

    paths = [Path(p) for p in path]
    mod_infos = get_info_for_modules(paths, exclude)
    modules = load_modules(mod_infos)
    unfiltered_tests = get_tests_in_modules(modules, capture_output)
    plugins.hook.preprocess_tests(config=config, collected_tests=unfiltered_tests)
    filtered_tests = filter_tests(unfiltered_tests, query=search, tag_expr=tags)
    if config.order == "random":
        shuffle(filtered_tests)

    tests = rewrite_assertions_in_tests(filtered_tests)

    time_to_collect_secs = default_timer() - start_run

    suite = Suite(tests=tests)
    test_results = suite.generate_test_runs(dry_run=dry_run)
    console.print(
        SessionPrelude(
            time_to_collect_secs=time_to_collect_secs,
            num_tests_collected=suite.num_tests_with_parameterisation,
            num_fixtures_collected=len(_DEFINED_FIXTURES),
            config_path=config_path,
        )
    )
    writer = SimpleTestResultWrite(
        suite=suite,
        test_output_style=test_output_style,
        progress_styles=progress_styles,
        config_path=config_path,
        show_diff_symbols=show_diff_symbols,
    )
    for renderable in print_before:
        console.print(renderable)
    test_results = writer.output_all_test_results(test_results, fail_limit=fail_limit)
    exit_code = get_exit_code(test_results)
    time_taken = default_timer() - start_run

    render_afters: Tuple[ConsoleRenderable] = plugins.hook.after_session(
        config=config, test_results=test_results, status_code=exit_code
    )
    for renderable in render_afters:
        console.print(renderable)

    writer.output_test_result_summary(test_results, time_taken, show_slowest)
    sys.exit(exit_code.value)


@run.command()
@config_option
@path_option
@exclude_option
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


@run.command()
@click.pass_context
def completions(ctx: click.Context):
    shell, path = click_completion.core.install()
    click.echo(f"{shell} completion installed in {path}")
    ctx.exit(0)
