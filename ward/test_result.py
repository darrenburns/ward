from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from colorama import Back, Fore, Style, init

from ward.test import Test

init()


class TestOutcome(Enum):
    PASS = auto()
    FAIL = auto()
    SKIP = auto()


@dataclass
class TestResult:
    test: Test
    outcome: TestOutcome
    error: Optional[Exception]
    message: str

    def __str__(self):
        if self.outcome == TestOutcome.PASS:
            status = f"{Back.GREEN}{Fore.BLACK} PASS {Style.RESET_ALL}"
        elif self.outcome == TestOutcome.SKIP:
            status = f"{Back.YELLOW}{Fore.BLACK} SKIP {Style.RESET_ALL}"
        else:
            status = f"{Back.RED}{Fore.BLACK} FAIL {Style.RESET_ALL}"

        test_name = f"{Fore.LIGHTBLACK_EX}{self.test.module.__name__}.{Fore.WHITE}{self.test.name}{Style.RESET_ALL}"
        params = ", ".join(list(self.test.deps()))
        params_coloured = f"({Fore.LIGHTBLACK_EX}{params}{Style.RESET_ALL})"
        return f"{status} {test_name}{params_coloured}"
