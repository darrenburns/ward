import sys
import traceback
from itertools import cycle
from typing import Generator

from blessings import Terminal
from colorama import Fore, Style

from python_tester.fixtures import TestSetupError
from python_tester.suite import Suite
from python_tester.test_result import TestResult

HEADER = "python-tester v0.0.1"


def write_test_result(str_to_write: str, term: Terminal):
    write_over_line(str_to_write, 2, term)


def write_over_progress_bar(green_pct: float, red_pct: float, term: Terminal):
    num_green_bars = int(green_pct * term.width)
    num_red_bars = int(red_pct * term.width)

    # Deal with rounding, converting to int could leave us with 1 bar less, so make it green
    if term.width - num_green_bars - num_red_bars == 1:
        num_green_bars += 1

    bar = term.red("█" * num_red_bars) + term.green("█" * num_green_bars)
    write_over_line(bar, 1, term)


def write_over_line(str_to_write: str, offset_from_bottom: int, term: Terminal):
    esc_code_rhs_margin = 28  # chars that are part of escape code, but NOT actually printed.
    with term.location(None, term.height - offset_from_bottom):
        right_margin = max(0, term.width - len(str_to_write) + esc_code_rhs_margin) * " "
        sys.stdout.write(f"{str_to_write}{right_margin}")
        sys.stdout.flush()


def reset_cursor(term: Terminal):
    print(term.normal_cursor())
    print(term.move(term.height - 1, 0))


def write_test_results_to_terminal(
    suite: Suite, term: Terminal, test_results: Generator[TestResult, None, None]
):
    # Fixtures are now loaded (since the modules have been loaded)
    print(term.hide_cursor())
    print("\n")
    write_over_line(
        f"{Fore.CYAN}[{HEADER}] Discovered {suite.num_tests} tests and "
        f"{suite.num_fixtures} fixtures.\nRunning tests...",
        4,
        term,
    )
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

            if isinstance(result.error, AssertionError):
                # TODO: Handle case where test assertion failed.
                pass

        write_test_result(str(result), term)

        pass_pct = passed / (passed + failed)
        fail_pct = 1.0 - pass_pct

        write_over_progress_bar(pass_pct, fail_pct, term)

        info_bar = (
            f"{Fore.CYAN}{next(spinner)} "
            f"{passed + failed} tests ran {Fore.LIGHTBLACK_EX}|{Fore.CYAN} "
            f"{failed} tests failed {Fore.LIGHTBLACK_EX}|{Fore.CYAN} "
            f"{passed} tests passed {Fore.LIGHTBLACK_EX}|{Fore.CYAN} "
            f"{pass_pct * 100:.2f}% pass rate{Style.RESET_ALL}"
        )

        write_over_line(info_bar, 0, term)
    print()
    total = passed + failed
    if total == 0:
        write_over_line(term.cyan_bold(f"No tests found."), 1, term)
    if failing_test_results:
        for test_result in failing_test_results:
            test_name = test_result.test.name
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
                write_over_line(str(err), 0, term)
            else:
                trc = traceback.format_exception(None, err, err.__traceback__)
                write_over_line("".join(trc), 0, term)
    reset_cursor(term)
    print()
    print(info_bar)
