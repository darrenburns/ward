import argparse
import traceback
from itertools import cycle
from typing import Any, Dict

from blessings import Terminal
from colorama import Fore, Style

from python_tester.collect.fixtures import TestSetupError, fixture_registry
from python_tester.collect.modules import get_info_for_modules, load_modules
from python_tester.collect.tests import get_tests_in_modules
from python_tester.output.terminal import reset_cursor, write_over_line, write_over_progress_bar, write_test_result
from python_tester.runner.runner import run_tests

HEADER = "python-tester v0.0.1"


def setup_cmd_line():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="path of directory containing tests")
    return parser


def run():
    term = Terminal()

    cmd_line = setup_cmd_line()
    args: Dict[str, Any] = vars(cmd_line.parse_args())

    path_to_tests = args.get("path", ".") or "."

    mod_infos = get_info_for_modules(path_to_tests)
    modules = load_modules(mod_infos)
    tests = list(get_tests_in_modules(modules))
    test_results = run_tests(tests, fixture_registry)

    # Fixtures are now loaded (since the modules have been loaded)
    print(term.hide_cursor())
    print("\n")
    write_over_line(f"{Fore.CYAN}[{HEADER}] Discovered {len(tests)} tests and "
                    f"{len(fixture_registry)} fixtures.\nRunning tests...", 4, term)

    failing_test_results = []
    passed, failed = 0, 0
    spinner = cycle("⠁⠁⠉⠙⠚⠒⠂⠂⠒⠲⠴⠤⠄⠄⠤⠠⠠⠤⠦⠖⠒⠐⠐⠒⠓⠋⠉⠈⠈")
    info_bar = ""
    for result in test_results:
        if result.was_success:
            passed += 1
        else:
            failed += 1
            failing_test_results.append(result)

        write_test_result(str(result), term)

        pass_pct = passed / (passed + failed)
        fail_pct = 1.0 - pass_pct

        write_over_progress_bar(pass_pct, fail_pct, term)

        info_bar = f"{Fore.CYAN}{next(spinner)}" \
            f" {passed + failed} tests ran {Fore.LIGHTBLACK_EX}|{Fore.CYAN} " \
            f"{failed} tests failed {Fore.LIGHTBLACK_EX}|{Fore.CYAN} " \
            f"{passed} tests passed {Fore.LIGHTBLACK_EX}|{Fore.CYAN} " \
            f"{pass_pct * 100:.2f}% pass rate{Style.RESET_ALL}"

        write_over_line(info_bar, 0, term)

    print()

    total = passed + failed
    if total == 0:
        write_over_line(term.cyan_bold(f"No tests found in directory '{path_to_tests}'"), 1, term)

    if failing_test_results:
        for test_result in failing_test_results:
            test_name = test_result.test.get_test_name()
            test_result_heading = f"{term.cyan_bold}{test_name}{term.normal}"
            num_non_separator_chars = 4
            write_over_line(
                f"-- {test_result_heading}{term.dim} "
                f"{'-' * (term.width - num_non_separator_chars - len(test_name))}{term.normal}",
                0,
                term,
            )

            err = test_result.error
            if isinstance(err, TestSetupError):
                write_over_line(
                    str(err),
                    0,
                    term,
                )
            else:
                trc = traceback.format_exception(None, err, err.__traceback__)
                write_over_line(
                    "".join(trc),
                    0,
                    term,
                )

    reset_cursor(term)
    print()
    print(info_bar)


if __name__ == "__main__":
    run()
