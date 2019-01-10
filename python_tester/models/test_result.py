from typing import Optional

from termcolor import colored

from python_tester.models.test import Test


class TestResult:
    def __init__(self, test: Test, was_success: bool, error: Optional[Exception], message: str = None):
        self.test = test
        self.was_success = was_success
        self.error = error
        self.message = message

    def __str__(self):
        tick, cross = "\u2713", "\u2718"
        status = (
            colored(tick, color="green") if self.was_success else colored(cross, color="red")
        )
        test_name = colored(self.test.module.__name__ + "." + self.test.get_test_name(), color="green" if self.was_success else "red")
        additional = f"({self.message})" if self.message else ""
        return f"[{status}] {test_name} {additional}"
