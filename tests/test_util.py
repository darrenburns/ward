import os
import shutil
import tempfile
from pathlib import Path

from tests.test_suite import example_test
from ward import expect, test, using, fixture
from ward.testing import TestOutcome, TestResult, each
from ward.util import ExitCode, get_exit_code, truncate, outcome_to_colour, find_project_root


@test(
    "get_exit_code returns ExitCode.SUCCESS when PASS, SKIP and XFAIL in test results"
)
@using(example=example_test)
def _(example):
    test_results = [
        TestResult(test=example, outcome=TestOutcome.PASS),
        TestResult(test=example, outcome=TestOutcome.SKIP),
        TestResult(test=example, outcome=TestOutcome.XFAIL),
    ]
    exit_code = get_exit_code(test_results)

    expect(exit_code).equals(ExitCode.SUCCESS)


@test("get_exit_code returns ExitCode.SUCCESS when no test results")
def _():
    exit_code = get_exit_code([])

    expect(exit_code).equals(ExitCode.NO_TESTS_FOUND)


@test("get_exit_code returns ExitCode.FAILED when XPASS in test results")
def _(example=example_test):
    test_results = [
        TestResult(test=example, outcome=TestOutcome.XPASS),
        TestResult(test=example, outcome=TestOutcome.PASS),
    ]
    exit_code = get_exit_code(test_results)

    expect(exit_code).equals(ExitCode.FAILED)


@fixture
def s():
    return "hello world"


@test("truncate('{input}', num_chars={num_chars}) returns '{expected}'")
def _(
    input=s, num_chars=each(20, 11, 10, 5), expected=each(s, s, "hello w...", "he...")
):
    result = truncate(input, num_chars)
    expect(result).equals(expected)


@test("outcome_to_colour({outcome}) returns '{colour}'")
def _(
    outcome=each(TestOutcome.PASS, TestOutcome.SKIP, TestOutcome.FAIL, TestOutcome.XFAIL, TestOutcome.XPASS),
    colour=each("green", "blue", "red", "magenta", "yellow"),
):
    expect(outcome_to_colour(outcome)).equals(colour)


@test("find_project_root returns the root dir if no paths supplied")
def _():
    project_root = find_project_root([])
    fs_root = os.path.normpath(os.path.abspath(os.sep))
    expect(project_root).equals(Path(fs_root))


def make_project(root_file: str):
    tempdir = Path(tempfile.gettempdir())
    paths = [
        tempdir / "project/a/b/c",
        tempdir / "project/a/d",
        tempdir / "project/a",
    ]
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)

    root_file = tempdir / f"project/{root_file}"
    with open(root_file, "w+", encoding="utf-8"):
        yield tempdir / "project"
    shutil.rmtree(tempdir / "project")


@fixture
def fake_project_pyproject():
    yield from make_project("pyproject.toml")


@fixture
def fake_project_git():
    yield from make_project(".git")


@using(
    root_file=each("pyproject.toml", ".git"),
    project=each(fake_project_pyproject, fake_project_git),
)
@test("find_project_root finds project root with '{root_file}' file")
def _(root_file, project):
    root = find_project_root([project / "a/b/c", project / "a/d"])
    expect(root.resolve()).equals(project.resolve())
    expect((root / root_file).exists()).equals(True)
