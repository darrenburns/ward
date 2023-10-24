import platform
from dataclasses import dataclass
from modulefinder import ModuleFinder
from pathlib import Path
from pkgutil import ModuleInfo
from types import ModuleType
from unittest import mock

from cucumber_tag_expressions import parse

from tests.utilities import make_project
from ward import fixture, test
from ward._collect import (
    PackageData,
    _build_package_data,
    _get_module_path,
    _handled_within,
    _is_excluded_module,
    _remove_excluded_paths,
    filter_fixtures,
    filter_tests,
    is_test_module,
)
from ward.fixtures import Fixture
from ward.testing import Test, each, skip


def named():
    assert "fox" == "fox"


@fixture
def named_test():
    return Test(fn=named, module_name="my_module")


@fixture
def tests_to_search(named_test=named_test):
    return [named_test]


@test("__filter_tests__ matches on qualified test name")
def _(tests=tests_to_search, named=named_test):
    results = filter_tests(tests, query="my_module.named")
    assert list(results) == [named]


@test("filter_tests matches on test name alone")
def _(tests=tests_to_search, named=named_test):
    results = filter_tests(tests, query="named")
    assert list(results) == [named]


@test("filter_tests `query='fox'` returns tests with `'fox'` in the body")
def _(tests=tests_to_search, named=named_test):
    results = filter_tests(tests, query="fox")
    assert list(results) == [named]


@test("filter_tests returns an empty list when no tests match query")
def _(tests=tests_to_search):
    assert [] == filter_tests(tests, query="92qj3f9i")


@test("filter_tests when tags match simple tag expression")
def _():
    apples = Test(fn=named, module_name="", tags=["apples"])
    bananas = Test(fn=named, module_name="", tags=["bananas"])
    results = list(filter_tests([apples, bananas], tag_expr=parse("apples")))
    assert results == [apples]


@test("filter_tests when tags match complex tag expression")
def _():
    one = Test(fn=named, module_name="", tags=["apples", "bananas"])
    two = Test(fn=named, module_name="", tags=["bananas", "carrots"])
    three = Test(fn=named, module_name="", tags=["bananas"])
    tag_expr = parse("apples or bananas and not carrots")
    results = list(filter_tests([one, two, three], tag_expr=tag_expr))
    assert results == [one, three]


@test("filter_tests when both query and tag expression match a test")
def _():
    one = Test(fn=named, module_name="one", tags=["apples"])
    two = Test(fn=named, module_name="two", tags=["apples"])
    tag_expr = parse("apples")
    results = list(filter_tests([one, two], query="two", tag_expr=tag_expr))
    # Both tests match the tag expression, but only two matches the search query
    # because the query matches the module name for the test.
    assert results == [two]


@test("filter_tests when a test is defined with an empty tag list doesnt match")
def _():
    t = Test(fn=named, module_name="", tags=[])
    tag_expr = parse("apples")
    results = list(filter_tests([t], tag_expr=tag_expr))
    assert results == []


@test("filter_tests matches all tags when a tag expression is an empty string")
def _():
    t = Test(fn=named, module_name="", tags=["apples"])
    tag_expr = parse("")
    results = list(filter_tests([t], tag_expr=tag_expr))
    assert results == [t]


@test("filter_tests returns [] when the tag expression matches no tests")
def _():
    one = Test(fn=named, module_name="one", tags=["apples"])
    two = Test(fn=named, module_name="two", tags=["bananas"])
    tag_expr = parse("carrots")
    results = list(filter_tests([one, two], tag_expr=tag_expr))
    assert results == []


@fixture
def named_fixture():
    pass


@fixture
def marker_fixture():
    return "marker"


@test("filter_fixtures on empty list returns empty list")
def _():
    assert list(filter_fixtures([])) == []


@test("filter_fixtures matches anything with empty query and paths")
def _():
    fixtures = [Fixture(f) for f in [named_fixture, marker_fixture]]
    assert list(filter_fixtures(fixtures)) == fixtures


@test("filter_fixtures matches 'named_fixture' by name query {query!r}")
def _(query=each("named_fixture", "named", "fixture", "med_fix")):
    fixtures = [Fixture(f) for f in [named_fixture]]
    assert list(filter_fixtures(fixtures, query=query)) == fixtures


@test("filter_fixtures matches 'named_fixture' by module name query on {query!r}")
def _(query=each("test", "test_collect", "collect", "t_coll")):
    fixtures = [Fixture(f) for f in [named_fixture]]
    assert list(filter_fixtures(fixtures, query=query)) == fixtures


@test("filter_fixtures matches fixture by source query on {query!r}")
def _(query=each("marker", "mark", "ret", "return", '"')):
    fixtures = [Fixture(f) for f in [named_fixture, marker_fixture]]
    assert list(filter_fixtures(fixtures, query=query)) == [Fixture(marker_fixture)]


@test("filter_fixtures excludes fixtures when querying for {query!r}")
def _(query=each("echo", "foobar", "wizbang")):
    fixtures = [Fixture(f) for f in [named_fixture, marker_fixture]]
    assert list(filter_fixtures(fixtures, query=query)) == []


THIS_FILE = Path(__file__)


@test("filter_fixtures matches fixture by path on {path}")
def _(path=each(THIS_FILE, THIS_FILE.parent, THIS_FILE.parent.parent)):
    fixtures = [Fixture(f) for f in [named_fixture]]
    assert list(filter_fixtures(fixtures, paths=[path])) == fixtures


@test("filter_fixtures excludes by path on {path}")
def _(path=each(THIS_FILE.parent / "the-fixture-is-not-in-this-file.py")):
    fixtures = [Fixture(f) for f in [named_fixture]]
    assert list(filter_fixtures(fixtures, paths=[path])) == []


@test("is_test_module(<module: '{module_name}'>) returns {rv}")
def _(module_name=each("test_apples", "apples"), rv=each(True, False)):
    module = ModuleInfo(ModuleFinder(), module_name, False)
    assert is_test_module(module) == rv


PATH = Path("path/to/test_mod.py")


class StubModuleFinder:
    def find_spec(self, module_name: str):
        return StubSourceFileLoader()


@dataclass
class StubSourceFileLoader:
    origin: Path = PATH


@fixture
def test_module():
    return ModuleInfo(StubModuleFinder(), PATH.stem, False)


@test("get_module_path returns the path of the module")
def _(mod=test_module):
    assert _get_module_path(mod) == PATH


@test("is_excluded_module({mod.name}) is True for {excludes}")
def _(
    mod=test_module,
    excludes=str(PATH),
):
    assert _is_excluded_module(mod, [excludes])


@test("is_excluded_module({mod.name}) is False for {excludes}")
def _(mod=test_module, excludes=each("abc", "/path/to", "/path")):
    assert not _is_excluded_module(mod, exclusions=[excludes])


@fixture
def paths_to_py_files():
    return [
        Path("/a/b/c.py"),
        Path("/a/b/d/e.py"),
        Path("/a/b/d/f/g/h.py"),
    ]


for path_to_exclude in ["/a", "/a/", "/a/b", "/a/b/"]:

    @test("remove_excluded_paths removes {exclude} from list of paths")
    def _(exclude=path_to_exclude, paths=paths_to_py_files):
        assert _remove_excluded_paths(paths, [exclude]) == []


@test(
    "remove_excluded_paths removes correct files when exclusions relative to each other"
)
def _(paths=paths_to_py_files):
    assert _remove_excluded_paths(paths, ["/a/b/d", "/a/b/d/", "/a/b/d/f"]) == [
        Path("/a/b/c.py")
    ]


@test("remove_excluded_paths removes individually specified files")
def _(paths=paths_to_py_files):
    assert _remove_excluded_paths(paths, ["/a/b/d/e.py", "/a/b/d/f/g/h.py"]) == [
        Path("/a/b/c.py")
    ]


@test("remove_excluded_paths can remove mixture of files and dirs")
def _(paths=paths_to_py_files):
    assert _remove_excluded_paths(paths, ["/a/b/d/e.py", "/a/b/d/f/g/"]) == [
        Path("/a/b/c.py")
    ]


@fixture
def project():
    yield from make_project("module.py")


@test("handled_within({mod}, {search}) is True")
def _(
    root: Path = project, search=each("", "/", "a", "a/b", "a/b/c"), mod="a/b/c/d/e.py"
):
    module_path = root / mod
    assert _handled_within(module_path, [root / search])


@test("handled_within({mod}, {search}) is False")
def _(
    root: Path = project,
    search=each("x/y/z", "test_a.py", "a/b.py", "a/b/c/d/e.py"),
    mod="a/b/c/d/e.py",
):
    module_path = root / mod
    assert not _handled_within(module_path, [root / search])


@skip("Skipped on Windows", when=platform.system() == "Windows")
@test("_build_package_data constructs correct package data")
def _():
    from ward._collect import Path as ImportedPath

    m = ModuleType(name="")
    m.__file__ = "/foo/bar/baz/test_something.py"
    patch_is_dir = mock.patch.object(ImportedPath, "is_dir", return_value=True)
    # The intention of the side_effects below is to make `baz` and `bar` directories
    # contain __init__.py files. It's not clean, but it does test the behaviour well.
    patch_exists = mock.patch.object(
        ImportedPath, "exists", side_effect=[True, True, False]
    )
    with patch_is_dir, patch_exists:
        assert _build_package_data(m) == PackageData(
            pkg_name="bar.baz", pkg_root=Path("/foo")
        )


@skip("Skipped on Unix", when=platform.system() != "Windows")
@test("_build_package_data constructs package name '{pkg}' from '{path}'")
def _():
    from ward._collect import Path as ImportedPath

    m = ModuleType(name="")
    m.__file__ = "\\foo\\bar\\baz\\test_something.py"
    patch_is_dir = mock.patch.object(ImportedPath, "is_dir", return_value=True)
    patch_exists = mock.patch.object(
        ImportedPath, "exists", side_effect=[True, True, False]
    )
    with patch_is_dir, patch_exists:
        pkg_data = _build_package_data(m)
        assert pkg_data.pkg_name == "bar.baz"
        assert str(pkg_data.pkg_root).endswith("foo")
