from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from ward.testing import Test


class TestOutcome(Enum):
    PASS = auto()
    FAIL = auto()
    SKIP = auto()
    XFAIL = auto()  # expected fail
    XPASS = auto()  # unexpected pass


@dataclass
class TestResult:
    test: Test
    """The `Test` object that this result corresponds to."""
    outcome: TestOutcome
    error: Optional[Exception] = None
    message: str = ""
    """The message that will blah"""
    captured_stdout: str = ""
    captured_stderr: str = ""
