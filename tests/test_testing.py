import asyncio
from collections import defaultdict
from pathlib import Path
from unittest import mock

import sys

from tests.utilities import FORCE_TEST_PATH, testable_test
from ward import Scope, raises
from ward.errors import ParameterisationError
from ward.fixtures import FixtureCache, fixture
from ward.models import WardMeta
from ward.testing import ParamMeta, Test, each, test, xfail


def f():
    assert 1 == 1


mod = "my_module"
t = Test(fn=f, module_name=mod)


@fixture
def anonymous_test():
    @testable_test
    def _():
        assert 1 == 1

    return Test(fn=_, module_name=mod)


@fixture
def dependent_test():
    def x():
        return 1

    def _(a=x):
        assert 1 == 1

    return Test(fn=_, module_name=mod)


@fixture()
def cache():
    return FixtureCache()


@test("Test.name should return the name of the function it wraps")
def _(anonymous_test=anonymous_test):
    assert anonymous_test.name == "_"


@test("Test.qualified_name should return `module_name.function_name`")
def _():
    assert t.qualified_name == f"{mod}.{f.__name__}"


@test("Test.qualified_name should return `module_name._` when test name is _")
def _(anonymous_test=anonymous_test):
    assert anonymous_test.qualified_name == f"{mod}._"


@test("Test.deps should return {} when test uses no fixtures")
def _(anonymous_test=anonymous_test):
    assert anonymous_test.deps() == {}


@test("Test.deps should return correct params when test uses fixtures")
def _(dependent_test=dependent_test):
    deps = dependent_test.deps()
    assert "a" in deps


@test("Test.has_deps should return True when test uses fixtures")
def _(dependent_test=dependent_test):
    assert dependent_test.has_deps


@test("Test.has_deps should return False when test doesn't use fixtures")
def _(anonymous_test=anonymous_test):
    assert not anonymous_test.has_deps


@test("Test.run should delegate to the function it wraps")
def _(cache: FixtureCache = cache):
    called_with = None
    call_kwargs = (), {}

    def func(key="val", **kwargs):
        nonlocal called_with, call_kwargs
        called_with = key
        call_kwargs = kwargs

    t = Test(fn=func, module_name=mod)
    t.run(cache)
    assert called_with == "val"
    assert call_kwargs == {"kwargs": {}}


@test("Test.run should delegate to coroutine function it wraps")
def _(cache: FixtureCache = cache):
    called_with = None
    call_kwargs = (), {}

    async def func(key="val", **kwargs):
        nonlocal called_with, call_kwargs
        called_with = key
        call_kwargs = kwargs

    t = Test(fn=func, module_name=mod)
    t.run(cache)
    assert called_with == "val"
    assert call_kwargs == {"kwargs": {}}


@fixture
async def one():
    await asyncio.sleep(0.00001)
    yield 1


@fixture(scope="module")
async def two():
    await asyncio.sleep(0.00001)
    return 2


@fixture
def three():
    return 3


@xfail("intentional failure")
@test("async/await failing test")
async def _(one=one, two=two):
    await asyncio.sleep(0.0001)
    assert one + two == 999


@test("async/await passing test")
async def _(one=one, two=two, three=three):
    assert one + two == three


@test("Test.is_parameterised should return True for parameterised test")
def _():
    def parameterised_test(a=each(1, 2, 3), b="a value"):
        pass

    t = Test(fn=parameterised_test, module_name=mod)

    assert t.is_parameterised == True


@test("Test.is_parameterised should return False for standard tests")
def _():
    def test():
        pass

    t = Test(fn=test, module_name=mod)

    assert not t.is_parameterised


@test("Test.scope_key_from(Scope.Test) returns the test ID")
def _(t: Test = anonymous_test):
    scope_key = t.scope_key_from(Scope.Test)

    assert scope_key == t.id


@test("Test.scope_key_from(Scope.Module) returns the path of the test module")
def _(t: Test = anonymous_test):
    scope_key = t.scope_key_from(Scope.Module)

    assert scope_key == testable_test.path


@test("Test.scope_key_from(Scope.Global) returns Scope.Global")
def _(t: Test = anonymous_test):
    scope_key = t.scope_key_from(Scope.Global)

    assert scope_key == Scope.Global


@test("Test.get_parameterised_instances returns [self] if not parameterised")
def _():
    def test():
        pass

    t = Test(fn=test, module_name=mod)

    assert t.get_parameterised_instances() == [t]


@test("Test.get_parameterised_instances returns correct number of test instances")
def _():
    def test(a=each(1, 2), b=each(3, 4)):
        pass

    t = Test(fn=test, module_name=mod, capture_output=False)
    assert t.get_parameterised_instances() == [
        Test(
            id=mock.ANY,
            fn=t.fn,
            module_name=t.module_name,
            param_meta=ParamMeta(0, 2),
            sout=mock.ANY,
            serr=mock.ANY,
            capture_output=False,
        ),
        Test(
            id=mock.ANY,
            fn=t.fn,
            module_name=t.module_name,
            param_meta=ParamMeta(1, 2),
            sout=mock.ANY,
            serr=mock.ANY,
            capture_output=False,
        ),
    ]


@test("Test.get_parameterised_instances raises exception for arg count mismatch")
def _():
    def invalid_test(a=each(1, 2), b=each(3, 4, 5)):
        pass

    t = Test(fn=invalid_test, module_name=mod)

    with raises(ParameterisationError):
        t.get_parameterised_instances()


@testable_test
def i_print_something():
    print("out")
    sys.stderr.write("err")
    raise Exception


@test("stdout/stderr are captured by default when a test is called")
def _(cache: FixtureCache = cache):
    t = Test(fn=i_print_something, module_name="")
    result = t.run(cache)
    assert result.captured_stdout == "out\n"
    assert result.captured_stderr == "err"


@test("stdout/stderr are not captured when Test.capture_output = False")
def _(cache: FixtureCache = cache):
    t = Test(fn=i_print_something, module_name="", capture_output=False)
    result = t.run(cache)
    assert result.captured_stdout == ""
    assert result.captured_stderr == ""


@fixture
def example_test():
    def func():
        assert 1 < 2

    return func


@test("@test attaches correct WardMeta to test function it wraps")
def _(func=example_test):
    out_func = testable_test(func)

    assert out_func.ward_meta == WardMeta(
        marker=None,
        description="testable test description",
        is_fixture=False,
        scope=Scope.Test,
        bound_args=None,
        path=FORCE_TEST_PATH,
    )


@test("@test doesn't attach WardMeta to functions in non-test modules")
def _(func=example_test):
    func.__module__ = "blah"
    out_func = test("test")(func)

    assert not hasattr(out_func, "ward_meta")


@test("@test attaches WardMeta to functions in modules ending in '_test'")
def _(func=example_test):
    func.__module__ = "its_a_test"
    out_func = test("test")(func)

    assert hasattr(out_func, "ward_meta")


@test("@test doesn't attach WardMeta to tests from imported modules")
def _(func=example_test):
    # There is an underlying assumption here that a test from an
    # imported module will always have a __module__ containing a "."
    func.__module__ = "test_contains.dot_test"
    out_func = test("test")(func)

    assert not hasattr(out_func, "ward_meta")


@test("@test collects tests into specified data structure")
def _(func=example_test):
    dest = defaultdict(list)
    path = Path("p")
    test("test", _collect_into=dest, _force_path=path)(func)
    assert dest[path.absolute()] == [func]


@test("@test doesn't collect items from non-test modules")
def _(func=example_test):
    func.__module__ = "run"
    dest = defaultdict(list)
    path = Path("p")
    test("test", _collect_into=dest, _force_path=path)(func)
    assert len(dest) == 0


@test("@test doesn't tests imported from another test module")
def _(func=example_test):
    func.__module__ = "test_contains.dot_test"
    dest = defaultdict(list)
    path = Path("p")
    test("test", _collect_into=dest, _force_path=path)(func)
    assert len(dest) == 0
