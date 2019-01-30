from typing import Optional

from colorama import init, Fore, Back, Style

from python_tester.models.test import Test

init()

class TestResult:
    def __init__(self, test: Test, was_success: bool, error: Optional[Exception], message: str = None):
        self.test = test
        self.was_success = was_success
        self.error = error
        self.message = message

    def __str__(self):
        pass_str, fail_str = f"PASS", f"FAIL"
        status = (
            f"{Back.GREEN}{Fore.BLACK} {pass_str} {Style.RESET_ALL}" if self.was_success else f"{Back.RED}{Fore.BLACK} {fail_str} {Style.RESET_ALL}"
        )
        test_name = f"{Fore.LIGHTBLACK_EX}{self.test.module.__name__}" + "." + f"{Fore.WHITE}{self.test.get_test_name()}{Style.RESET_ALL}"
        # additional = f"({self.message})" if self.message else ""
        return f"{status} {test_name}"
