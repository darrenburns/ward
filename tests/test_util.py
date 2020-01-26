import os
import shutil
import tempfile
from pathlib import Path

from ward import test, using, fixture
from ward.testing import each
from ward.util import (
    truncate,
    find_project_root,
)


@fixture
def s():
    return "hello world"


@test("truncate('{input}', num_chars={num_chars}) returns '{expected}'")
def _(
    input=s, num_chars=each(20, 11, 10, 5), expected=each(s, s, "hello w...", "he...")
):
    result = truncate(input, num_chars)
    assert result == expected


@test("find_project_root returns the root dir if no paths supplied")
def _():
    project_root = find_project_root([])
    fs_root = os.path.normpath(os.path.abspath(os.sep))
    assert project_root == Path(fs_root)


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
    assert root.resolve() == project.resolve()
    assert (root / root_file).exists() == True
