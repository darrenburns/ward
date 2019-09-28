import sys
import traceback
from dataclasses import dataclass
from enum import Enum
from itertools import cycle
from typing import Iterable

from blessings import Terminal
from colorama import Fore, Style

from ward.expect import ExpectationFailed
from ward.fixtures import TestSetupError
from ward.suite import Suite
from ward.test_result import TestResult

HEADER = f"ward"


def write_test_failure_output(term, test_result):
    # Header of failure output
    test_name = test_result.test.name
    test_module = test_result.test.module.__name__
    error_text = f"[{type(test_result.error).__name__}]"
    test_result_heading = f"Test '{test_module}.{test_name}' failed:"
    write_over_line(
        f"{Fore.RED}{test_result_heading} ",
        0,
        term,
    )
    err = test_result.error

    # Body of failure output, depends on how the test failed
    if isinstance(err, TestSetupError):
        write_over_line(str(err), 0, term)
    elif isinstance(err, ExpectationFailed):
        print()
        write_over_line(f"  Expectations for value {err.history[0].this}:", 0, term)
        for expect in err.history:
            if expect.success:
                result_marker = f"[ {Fore.GREEN}✓{Style.RESET_ALL} ]{Fore.GREEN}"
            else:
                result_marker = f"[ {Fore.RED}✗{Style.RESET_ALL} ]{Fore.RED}"
            write_over_line(f"    {result_marker} it {expect.op} {expect.that}{Style.RESET_ALL}", 0, term)
    else:
        trc = traceback.format_exception(None, err, err.__traceback__)
        write_over_line("".join(trc), 0, term)


def write_test_result(test_result: TestResult, term: Terminal):
    write_over_line(str(test_result), 2, term)


def write_over_progress_bar(green_pct: float, red_pct: float, term: Terminal):
    num_green_bars = int(green_pct * term.width)
    num_red_bars = int(red_pct * term.width)

    # Deal with rounding, converting to int could leave us with 1 bar less, so make it green
    if term.width - num_green_bars - num_red_bars == 1:
        num_green_bars += 1

    bar = term.red("█" * num_red_bars) + term.green("█" * num_green_bars)
    write_over_line(bar, 1, term)


def write_over_line(str_to_write: str, offset_from_bottom: int, term: Terminal):
    # TODO: Smarter way of tracking margins based on escape codes used.
    esc_code_rhs_margin = (
        37
    )  # chars that are part of escape code, but NOT actually printed. Yeah I know...
    with term.location(None, term.height - offset_from_bottom):
        right_margin = max(0, term.width - len(str_to_write) + esc_code_rhs_margin) * " "
        sys.stdout.write(f"{str_to_write}{right_margin}")
        sys.stdout.flush()


def reset_cursor(term: Terminal):
    print(term.normal_cursor())
    print(term.move(term.height - 1, 0))


class ExitCode(Enum):
    SUCCESS = 0
    TEST_FAILED = 1


@dataclass
class TestResultWriter:
    suite: Suite
    terminal: Terminal
    test_results: Iterable[TestResult]

    def write_test_results_to_terminal(self) -> ExitCode:
        print(self.terminal.hide_cursor())
        print("\n")
        write_over_line(
            f"{Fore.CYAN}[{HEADER}] Discovered {self.suite.num_tests} tests and "
            f"{self.suite.num_fixtures} fixtures.\nRunning {self.suite.num_tests} tests...",
            4,
            self.terminal,
        )

        failing_test_results = []
        passed, failed = 0, 0
        spinner = cycle("⠁⠁⠉⠙⠚⠒⠂⠂⠒⠲⠴⠤⠄⠄⠤⠠⠠⠤⠦⠖⠒⠐⠐⠒⠓⠋⠉⠈⠈")
        info_bar = ""
        for result in self.test_results:
            if result.was_success:
                passed += 1
            else:
                failed += 1
                failing_test_results.append(result)

            write_test_result(result, self.terminal)

            pass_pct = passed / (passed + failed)
            fail_pct = 1.0 - pass_pct

            write_over_progress_bar(pass_pct, fail_pct, self.terminal)

            info_bar = (
                f"{Fore.CYAN}{next(spinner)} "
                f"{passed + failed} tests ran {Fore.LIGHTBLACK_EX}|{Fore.CYAN} "
                f"{failed} tests failed {Fore.LIGHTBLACK_EX}|{Fore.CYAN} "
                f"{passed} tests passed {Fore.LIGHTBLACK_EX}|{Fore.CYAN} "
                f"{pass_pct * 100:.2f}% pass rate{Style.RESET_ALL}"
            )

            write_over_line(info_bar, 0, self.terminal)
        total = passed + failed
        if total == 0:
            write_over_line(self.terminal.cyan_bold(f"No tests found."), 1, self.terminal)
        if failing_test_results:
            for test_result in failing_test_results:
                write_test_failure_output(self.terminal, test_result)

        reset_cursor(self.terminal)
        if failing_test_results:
            print(info_bar)
            return ExitCode.TEST_FAILED

        return ExitCode.SUCCESS
