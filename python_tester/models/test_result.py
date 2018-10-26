from typing import Optional

from termcolor import colored


class TestResult:
    def __init__(self, test_name: str, was_success: bool, error: Optional[Exception], message: str = None):
        self.test_name = test_name
        self.was_success = was_success
        self.error = error
        self.message = message

    def __str__(self):
        status = (
            colored("\u2713", color="green") if self.was_success else colored("\u2718", color="red")
        )
        test_name = colored(self.test_name, color="green" if self.was_success else "red")
        additional = f"({self.message})" if self.message else ""
        return f"[{status}] {test_name} {additional}"
