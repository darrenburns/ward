from pathlib import Path
from timeit import default_timer
from typing import Tuple, Optional, List

from ward.collect import (
    get_info_for_modules,
    load_modules,
    get_tests_in_modules,
    search_generally,
)
from ward.rewrite import rewrite_assertions_in_tests
from ward.suite import Suite
from ward.terminal import SimpleTestResultWrite
from ward.testing import TestResult


def run_tests_at_path_and_output_results(
    path: Tuple[str],
    test_output_style: str = "test-per-line",
    search: Optional[str] = None,
    capture_output: bool = True,
    fail_limit: Optional[int] = None,
    order: str = "standard",
) -> List[TestResult]:
    start_run = default_timer()
    paths = [Path(p) for p in path]
    mod_infos = get_info_for_modules(paths)
    modules = list(load_modules(mod_infos))
    unfiltered_tests = get_tests_in_modules(modules, capture_output)
    tests = list(search_generally(unfiltered_tests, query=search))
    tests = rewrite_assertions_in_tests(tests)
    time_to_collect = default_timer() - start_run
    suite = Suite(tests=tests)
    test_results = suite.generate_test_runs(order=order)
    writer = SimpleTestResultWrite(suite=suite, test_output_style=test_output_style)
    results = writer.output_all_test_results(
        test_results, time_to_collect=time_to_collect, fail_limit=fail_limit
    )
    time_taken = default_timer() - start_run
    writer.output_test_result_summary(results, time_taken)
    return results
