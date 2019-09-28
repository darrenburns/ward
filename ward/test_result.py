from dataclasses import dataclass
from typing import Optional

from colorama import Back, Fore, Style, init

from ward.test import Test

init()


@dataclass
class TestResult:
    test: Test
    was_success: bool
    error: Optional[Exception]
    message: str

    def __str__(self):
        pass_str, fail_str = "PASS", "FAIL"

        if self.was_success:
            status = f"{Back.GREEN}{Fore.BLACK} {pass_str} {Style.RESET_ALL}"
        else:
            status = f"{Back.RED}{Fore.BLACK} {fail_str} {Style.RESET_ALL}"

        test_name = f"{Fore.LIGHTBLACK_EX}{self.test.module.__name__}.{Fore.WHITE}{self.test.name}{Style.RESET_ALL}"
        params = ", ".join(list(self.test.deps()))
        params_coloured = f"({Fore.LIGHTBLACK_EX}{params}{Style.RESET_ALL})"
        return f"{status} {test_name}{params_coloured}"
