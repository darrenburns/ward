from dataclasses import dataclass
from modulefinder import ModuleFinder
from pathlib import Path
from pkgutil import ModuleInfo

from tests.test_util import make_project
from ward import test, fixture, raises
from ward.collect import (
    search_generally,
    is_test_module,
    get_module_path,
    is_excluded_module,
    remove_excluded_paths,
    handled_within,
)
from ward.testing import Test, each


def named():
    assert "fox" == "fox"


@fixture
def named_test():
    return Test(fn=named, module_name="my_module")


@fixture
def tests_to_search(named_test=named_test):
    return [named_test]


@test("search_generally matches on qualified test name")
def _(tests=tests_to_search, named=named_test):
    results = search_generally(tests, query="my_module.named")
    assert list(results) == [named]


@test("search_generally matches on test name alone")
def _(tests=tests_to_search, named=named_test):
    results = search_generally(tests, query="named")
    assert list(results) == [named]


@test("search_generally query='fox' returns tests with 'fox' in the body")
def _(tests=tests_to_search, named=named_test):
    results = search_generally(tests, query="fox")
    assert list(results) == [named]


@test("search_generally returns an empty generator when no tests match query")
def _(tests=tests_to_search):
    results = search_generally(tests, query="92qj3f9i")
    with raises(StopIteration):
        next(results)


@test("is_test_module(<module: '{module_name}'>) returns {rv}")
def _(
    module_name=each("test_apples", "apples"), rv=each(True, False),
):
    module = ModuleInfo(ModuleFinder(), module_name, False)
    assert is_test_module(module) == rv


PATH = Path("path/to/test_mod.py")


class StubModuleFinder:
    def find_module(self, module_name: str):
        return StubSourceFileLoader()


@dataclass
class StubSourceFileLoader:
    path: str = PATH


@fixture
def test_module():
    return ModuleInfo(StubModuleFinder(), PATH.stem, False)


@test("get_module_path returns the path of the module")
def _(mod=test_module):
    assert get_module_path(mod) == PATH


@test("is_excluded_module({mod.name}) is True for {excludes}")
def _(
    mod=test_module,
    excludes=each(
        "*", "*/**.py", str(PATH), "**/test_mod.py", "path/to/*", "path/*/*.py",
    ),
):
    assert is_excluded_module(mod, [excludes])


@test("is_excluded_module({mod.name}) is False for {excludes}")
def _(mod=test_module, excludes=each("abc", str(PATH.parent))):
    assert not is_excluded_module(mod, [excludes])


@test("remove_excluded_paths removes exclusions from list of paths")
def _():
    paths = [
        Path("/a/b/c.py"),
        Path("/a/b/"),
    ]
    excludes = ["**/*.py"]
    assert remove_excluded_paths(paths, excludes) == [paths[1]]


@fixture
def project():
    yield from make_project("module.py")


@test("handled_within({mod}, {search}) is True")
def _(
    root: Path = project, search=each("", "/", "a", "a/b", "a/b/c"), mod="a/b/c/d/e.py",
):
    module_path = root / mod
    assert handled_within(module_path, [root / search])


@test("handled_within({mod}, {search}) is False")
def _(
    root: Path = project,
    search=each("x/y/z", "a.py", "a/b.py", "a/b/c/d/e.py"),
    mod="a/b/c/d/e.py",
):
    module_path = root / mod
    assert not handled_within(module_path, [root / search])
