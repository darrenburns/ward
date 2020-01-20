from modulefinder import ModuleFinder
from pkgutil import ModuleInfo

from ward import test, fixture, expect, raises
from ward.collect import search_generally, is_test_module
from ward.testing import Test, each


def named():
    expect("fox").equals("fox")


@fixture
def named_test():
    return Test(fn=named, module_name="my_module")


@fixture
def tests_to_search(named_test=named_test):
    return [named_test]


@test("search_generally matches on qualified test name")
def _(tests=tests_to_search, named=named_test):
    results = search_generally(tests, query="my_module.named")
    expect(list(results)).equals([named])


@test("search_generally matches on test name alone")
def _(tests=tests_to_search, named=named_test):
    results = search_generally(tests, query="named")
    expect(list(results)).equals([named])


@test("search_generally query='fox' returns tests with 'fox' in the body")
def _(tests=tests_to_search, named=named_test):
    results = search_generally(tests, query="fox")
    expect(list(results)).equals([named])


@test("search_generally returns an empty generator when no tests match query")
def _(tests=tests_to_search):
    results = search_generally(tests, query="92qj3f9i")
    with raises(StopIteration):
        next(results)


@test("is_test_module(<module: '{module_name}'>) returns {rv}")
def _(
    module_name=each("test_apples", "apples"),
    rv=each(True, False),
):
    module = ModuleInfo(ModuleFinder(), module_name, False)
    expect(is_test_module(module)).equals(rv)
