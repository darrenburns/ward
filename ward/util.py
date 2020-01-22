from enum import Enum
from pathlib import Path
from typing import Iterable

from ward.testing import TestOutcome, TestResult


class ExitCode(Enum):
    SUCCESS = 0
    FAILED = 1
    ERROR = 2
    NO_TESTS_FOUND = 3


def get_exit_code(results: Iterable[TestResult]) -> ExitCode:
    if not results:
        return ExitCode.NO_TESTS_FOUND

    if any(
        r.outcome == TestOutcome.FAIL or r.outcome == TestOutcome.XPASS for r in results
    ):
        exit_code = ExitCode.FAILED
    else:
        exit_code = ExitCode.SUCCESS
    return exit_code


def truncate(s: str, num_chars: int) -> str:
    suffix = "..." if len(s) > num_chars else ""
    return s[: num_chars - len(suffix)] + suffix


def outcome_to_colour(outcome: TestOutcome) -> str:
    return {
        TestOutcome.PASS: "green",
        TestOutcome.SKIP: "blue",
        TestOutcome.FAIL: "red",
        TestOutcome.XFAIL: "magenta",
        TestOutcome.XPASS: "yellow",
    }[outcome]


def find_project_root(paths: Iterable[Path]) -> Path:
    if not paths:
        return Path("/").resolve()

    common_base = min(path.resolve() for path in paths)
    if common_base.is_dir():
        common_base /= "child-of-base"

    # Check this common base and all of its parents for files
    # indicating the project root
    for directory in common_base.parents:
        if (directory / "pyproject.toml").is_file():
            return directory
        if (directory / ".git").exists():
            return directory
        if (directory / ".hg").is_dir():
            return directory

    return directory
