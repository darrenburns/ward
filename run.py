import argparse
import pkgutil
from itertools import cycle
from time import sleep
from typing import Any, Dict, Generator

from blessings import Terminal

from python_tester.collect.fixtures import fixture_registry
from python_tester.collect.modules import get_info_for_modules, load_modules
from python_tester.collect.tests import get_tests_in_modules
from python_tester.models.test_result import TestResult
from python_tester.output.terminal import write_test_result, write_over_progress_bar, write_over_line, reset_cursor
from python_tester.runner.runner import run_tests


HEADER = "python-tester v0.0.1"


def setup_cmd_line():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="path of directory containing tests")
    return parser


def is_test_module(module: pkgutil.ModuleInfo) -> bool:
    return module.name.startswith("test_")


def run():
    term = Terminal()

    cmd_line = setup_cmd_line()
    args: Dict[str, Any] = vars(cmd_line.parse_args())

    path_to_tests = args.get("path") or "."

    mod_infos = get_info_for_modules(path_to_tests)
    test_mod_infos = (info for info in mod_infos if is_test_module(info))
    modules = load_modules(test_mod_infos)
    tests = get_tests_in_modules(modules)
    test_results: Generator[TestResult, None, None] = run_tests(tests, fixture_registry)

    # Fixtures are now loaded (since the modules have been loaded)
    print(term.hide_cursor())
    print("\n")
    write_over_line(term.cyan_bold(HEADER), 4, term)

    failing_test_results = []
    passed, failed = 0, 0
    spinner = cycle("⠁⠁⠉⠙⠚⠒⠂⠂⠒⠲⠴⠤⠄⠄⠤⠠⠠⠤⠦⠖⠒⠐⠐⠒⠓⠋⠉⠈⠈")
    for result in test_results:
        # sleep(.1)
        if result.was_success:
            passed += 1
        else:
            failed += 1
            failing_test_results.append(result)

        write_test_result(str(result), term)

        pass_pct = passed / (passed + failed)
        fail_pct = 1.0 - pass_pct

        write_over_progress_bar(pass_pct, fail_pct, term)

        info_bar = term.cyan_bold(f"{next(spinner)}"
                                  f" {passed + failed} tests ran | "
                                  f"{failed} tests failed | "
                                  f"{passed} tests passed | "
                                  f"{pass_pct * 100:.2f}% success rate ")

        write_over_line(info_bar, 1, term)

        # sleep(0.1)

    total = passed + failed
    if total == 0:
        write_over_line(term.cyan_bold(f"No tests found in directory '{path_to_tests}'"), 1, term)

    if failing_test_results:
        print()
        for test_result in failing_test_results:
            output = test_result.test.get_test_name()

            print(output)
            print(test_result.error.__traceback__)

    reset_cursor(term)


if __name__ == "__main__":
    run()
