from enum import Enum
from typing import Iterable

from ward.testing import TestOutcome, TestResult


class ExitCode(Enum):
    SUCCESS = 0
    FAILED = 1
    ERROR = 2


def get_exit_code(results: Iterable[TestResult]) -> ExitCode:
    if any(
        r.outcome == TestOutcome.FAIL or r.outcome == TestOutcome.XPASS for r in results
    ):
        exit_code = ExitCode.FAILED
    else:
        exit_code = ExitCode.SUCCESS
    return exit_code
