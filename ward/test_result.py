from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from ward.test import Test


class TestOutcome(Enum):
    PASS = auto()
    FAIL = auto()
    SKIP = auto()
    XFAIL = auto()


@dataclass
class TestResult:
    test: Test
    outcome: TestOutcome
    error: Optional[Exception]
    message: str
