from timeit import default_timer

import click
import sys
from colorama import init
from cucumber_tag_expressions import parse as parse_tags
from cucumber_tag_expressions.model import Expression
from pathlib import Path
from typing import List, Optional, Tuple

from ward._ward_version import __version__
from ward.collect import (
    get_info_for_modules,
    get_tests_in_modules,
    load_modules,
    search_generally,
)
from ward.config import set_defaults_from_config, Config, CollectionStats
from ward.rewrite import rewrite_assertions_in_tests
from ward.suite import Suite
from ward.terminal import get_exit_code, SequentialResultWriter
from ward.testing import TestResult

init()

sys.path.append(".")


class SequentialTestRunner:
    def __init__(
        self, suite: Suite, config: Config, collection_stats: CollectionStats,
    ):
        self.suite = suite
        self.config = config
        self.collection_stats = collection_stats

    def run_all(self) -> List[TestResult]:
        result_generator = self.suite.result_generator(
            order=self.config.order, dry_run=self.config.dry_run
        )
        writer = SequentialResultWriter(
            collection_stats=self.collection_stats, config=self.config,
        )
        results = writer.output_all_test_results(
            result_generator, fail_limit=self.config.fail_limit
        )
        overall_time_taken = default_timer() - self.collection_stats.run_start
        writer.output_test_result_summary(results, time_taken=overall_time_taken)
        return results


@click.command(context_settings={"max_content_width": 100})
@click.option(
    "--search",
    help="Search test names, bodies, descriptions and module names for the search query and only run matching tests.",
)
@click.option(
    "--tags",
    help="Run tests matching tag expression (e.g. 'unit and not slow').\n",
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
    "--exclude",
    type=click.STRING,
    multiple=True,
    help="Paths to ignore while searching for tests. Accepts glob patterns.",
)
@click.option(
    "--capture-output/--no-capture-output",
    default=True,
    help="Enable or disable output capturing.",
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
@click.pass_context
def run(
    ctx: click.Context,
    path: Tuple[str],
    exclude: Tuple[str],
    search: Optional[str],
    tags: Optional[Expression],
    fail_limit: Optional[int],
    test_output_style: str,
    order: str,
    capture_output: bool,
    config: str,
    config_path: Optional[Path],
    show_slowest: int,
    dry_run: bool,
):
    run_start_time = default_timer()
    paths = [Path(p) for p in path]
    mod_infos = get_info_for_modules(paths, exclude)
    modules = list(load_modules(mod_infos))
    unfiltered_tests = get_tests_in_modules(modules, capture_output)
    tests = list(search_generally(unfiltered_tests, query=search, tag_expr=tags,))
    tests = rewrite_assertions_in_tests(tests)

    conf = Config(
        path=path,
        exclude=exclude,
        search=search,
        tag_expression=tags,
        fail_limit=fail_limit,
        test_output_style=test_output_style,
        order=order,
        capture_output=capture_output,
        config=config,
        config_path=config_path,
        show_slowest=show_slowest,
        dry_run=dry_run,
    )
    suite = Suite(tests=tests)
    time_taken = default_timer() - run_start_time

    collection_stats = CollectionStats(
        run_start_time, time_taken, number_of_tests=suite.num_tests,
    )
    runner = SequentialTestRunner(suite, conf, collection_stats)
    results = runner.run_all()

    exit_code = get_exit_code(results)

    sys.exit(exit_code.value)
