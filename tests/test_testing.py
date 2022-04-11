import asyncio
import sys
from collections import defaultdict
from pathlib import Path
from unittest import mock

from tests.utilities import FORCE_TEST_PATH, testable_test
from ward import raises
from ward._errors import ParameterisationError
from ward._fixtures import FixtureCache
from ward.fixtures import Fixture, fixture
from ward.models import CollectionMetadata, Scope, SkipMarker, XfailMarker
from ward.testing import (
    ParamMeta,
    Test,
    TestArgumentResolver,
    TestOutcome,
    TestResult,
    each,
    fixtures_used_directly_by_tests,
    skip,
    test,
    xfail,
)


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


@test("Test.name returns the name of the function it wraps")
def _(anonymous_test=anonymous_test):
    assert anonymous_test.name == "_"


@test("Test.path returns the path from the ward_meta of the wrapped function")
def _():
    @testable_test
    def test_fn():
        assert True

    t = Test(test_fn, "")

    assert t.path == FORCE_TEST_PATH


@test("Test.qualified_name returns `module_name.function_name`")
def _():
    assert t.qualified_name == f"{mod}.{f.__name__}"


@test("Test.qualified_name returns `module_name._` when test name is _")
def _(anonymous_test=anonymous_test):
    assert anonymous_test.qualified_name == f"{mod}._"


@test("Test.is_async_test returns True if the wrapped function is a coroutine function")
def _():
    @testable_test
    async def test_fn():
        assert True

    t = Test(test_fn, "")

    assert t.is_async_test


@test(
    "Test.is_async_test returns False if the wrapped function isn't a coroutine function"
)
def _():
    @testable_test
    def test_fn():
        assert True

    t = Test(test_fn, "")

    assert not t.is_async_test


@test("Test.deps returns {} when test uses no fixtures")
def _(anonymous_test=anonymous_test):
    assert anonymous_test.deps() == {}


@test("Test.deps returns correct params when test uses fixtures")
def _(dependent_test=dependent_test):
    deps = dependent_test.deps()
    assert "a" in deps


@test("Test.has_deps returns True when test uses fixtures")
def _(dependent_test=dependent_test):
    assert dependent_test.has_deps


@test("Test.has_deps returns False when test doesn't use fixtures")
def _(anonymous_test=anonymous_test):
    assert not anonymous_test.has_deps


@test("Test.run delegates to the function it wraps")
def _(cache: FixtureCache = cache):
    called_with = None
    call_kwargs = (), {}  # type: ignore[var-annotated]

    def func(key="val", **kwargs):
        nonlocal called_with, call_kwargs
        called_with = key
        call_kwargs = kwargs

    t = Test(fn=func, module_name=mod)
    t.run(cache)
    assert called_with == "val"
    assert call_kwargs == {"kwargs": {}}  # type: ignore[comparison-overlap]


@test("Test.run delegates to coroutine function it wraps")
def _(cache: FixtureCache = cache):
    called_with = None
    call_kwargs = (), {}  # type: ignore[var-annotated]

    async def func(key="val", **kwargs):
        nonlocal called_with, call_kwargs
        called_with = key
        call_kwargs = kwargs

    t = Test(fn=func, module_name=mod)
    t.run(cache)
    assert called_with == "val"
    assert call_kwargs == {"kwargs": {}}  # type: ignore[comparison-overlap]


@test("Test.run returns DRYRUN TestResult when dry_run == True")
def _(cache=cache):
    t = Test(fn=lambda: 1, module_name=mod)
    result = t.run(cache, dry_run=True)
    assert result == TestResult(t, outcome=TestOutcome.DRYRUN)


TRUTHY_PREDICATES = each(True, lambda: True, 1, "truthy string")
FALSY_PREDICATES = each(False, lambda: False, 0, "")


@test("Test.run returns *SKIP* TestResult, @skip(when={when})")
def _(cache=cache, when=TRUTHY_PREDICATES):
    t = Test(fn=lambda: 1, module_name=mod, marker=SkipMarker(when=when))
    result = t.run(cache)
    assert result == TestResult(t, outcome=TestOutcome.SKIP)


@test("Test.run returns *PASS* TestResult for passing test, @skip(when={when})")
def _(cache=cache, when=FALSY_PREDICATES):
    def test_fn():
        assert True

    t = Test(fn=test_fn, module_name=mod, marker=SkipMarker(when=when))
    result = t.run(cache)

    assert result == TestResult(t, outcome=TestOutcome.PASS)


@test("Test.run returns *FAIL* TestResult for failing test, @skip(when={when})")
def _(cache=cache, when=FALSY_PREDICATES):
    def test_fn():
        assert 1 == 2

    t = Test(fn=test_fn, module_name=mod, marker=SkipMarker(when=when))
    result = t.run(cache)

    assert result.test == t
    assert result.outcome == TestOutcome.FAIL


@test("Test.run returns *XFAIL* TestResult for failing test, @xfail(when={when})")
def _(cache=cache, when=TRUTHY_PREDICATES):
    def test_fn():
        assert 1 == 2

    t = Test(fn=test_fn, module_name=mod, marker=XfailMarker(when=when))
    result = t.run(cache)

    assert result.test == t
    assert result.outcome == TestOutcome.XFAIL


@test("Test.run returns *FAIL* TestResult for failing test, @xfail(when={when})")
def _(cache=cache, when=FALSY_PREDICATES):
    def test_fn():
        assert 1 == 2

    t = Test(fn=test_fn, module_name=mod, marker=XfailMarker(when=when))
    result = t.run(cache)

    assert result.test == t
    assert result.outcome == TestOutcome.FAIL


@test("Test.run returns *XPASS* TestResult for passing test, @xfail(when={when})")
def _(cache=cache, when=TRUTHY_PREDICATES):
    def test_fn():
        assert 1 == 1

    t = Test(fn=test_fn, module_name=mod, marker=XfailMarker(when=when))
    result = t.run(cache)

    assert result.test == t
    assert result.outcome == TestOutcome.XPASS


@test("@skip decorator (no parens version) sets correct SkipMarker")
def _():
    @skip
    @testable_test
    def test_fn():
        assert True

    assert test_fn.ward_meta.marker == SkipMarker()
    assert test_fn.ward_meta.marker.active


@test("@xfail decorator (no parens version) sets correct XfailMarker")
def _():
    @xfail
    @testable_test
    def test_fn():
        assert True

    assert test_fn.ward_meta.marker == XfailMarker()


@test("@skip() decorator (parens version, no args) sets correct SkipMarker")
def _(when=FALSY_PREDICATES):
    @skip(when=when)
    @testable_test
    def test_fn():
        assert True

    assert test_fn.ward_meta.marker == SkipMarker(when=when)


@test("@xfail() decorator (parens version, no args) sets correct XfailMarker")
def _():
    @xfail()
    @testable_test
    def test_fn():
        assert True

    assert test_fn.ward_meta.marker == XfailMarker()


@test("@skip('reason') decorator (parens version, non-kwarg) sets correct SkipMarker")
def _(when=FALSY_PREDICATES):
    @skip("reason", when=when)
    @testable_test
    def test_fn():
        assert True

    assert test_fn.ward_meta.marker == SkipMarker(reason="reason", when=when)


@test("@xfail('reason') decorator (parens version, non-kwarg) sets correct XfailMarker")
def _(when=FALSY_PREDICATES):
    @xfail("reason", when=when)
    @testable_test
    def test_fn():
        assert True

    assert test_fn.ward_meta.marker == XfailMarker(reason="reason", when=when)


@test("@skip(reason='reason') decorator (with kwargs) sets correct SkipMarker")
def _(when=FALSY_PREDICATES):
    @skip(reason="reason", when=when)
    @testable_test
    def test_fn():
        assert True

    assert test_fn.ward_meta.marker == SkipMarker(reason="reason", when=when)


@test("@xfail('reason') decorator (with kwargs) sets correct XfailMarker")
def _(when=FALSY_PREDICATES):
    @xfail(reason="reason", when=when)
    @testable_test
    def test_fn():
        assert True

    assert test_fn.ward_meta.marker == XfailMarker(reason="reason", when=when)


@test("Test.fail_with_error returns the expected TestResult")
def _():
    message = "error message"
    error = ZeroDivisionError(message)

    t = Test(lambda: 1, "")
    rv = t.fail_with_error(error=error)

    assert rv == TestResult(
        test=t, outcome=TestOutcome.FAIL, error=error, message=message
    )


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


@test("a test that exits {exit_code} is marked as {outcome}")
def _(exit_code=each(0, 1), outcome=each(TestOutcome.FAIL, TestOutcome.FAIL)):
    t = Test(fn=lambda: sys.exit(exit_code), module_name=mod)

    assert t.run(FixtureCache()).outcome is outcome


@test("Test.is_parameterised should return True for parameterised test")
def _():
    def parameterised_test(a=each(1, 2, 3), b="a value"):
        pass

    t = Test(fn=parameterised_test, module_name=mod)

    assert t.is_parameterised


@test("Test.is_parameterised should return False for standard tests")
def _():
    def test():
        pass

    t = Test(fn=test, module_name=mod)

    assert not t.is_parameterised


@test("Test.resolver returns the expected TestArgumentResolver")
def _():
    @testable_test
    def test_fn():
        assert True

    t = Test(test_fn, "", param_meta=ParamMeta(instance_index=123))

    assert t.resolver == TestArgumentResolver(t, iteration=123)


@test("Test.scope_key_from(Scope.Test) returns the test ID")
def _(t: Test = anonymous_test):
    scope_key = t.scope_key_from(Scope.Test)

    assert scope_key == t.id


@test("Test.scope_key_from(Scope.Module) returns the path of the test module")
def _(t: Test = anonymous_test):
    scope_key = t.scope_key_from(Scope.Module)

    assert scope_key == testable_test.path  # type: ignore[attr-defined]


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


@test("@test attaches correct CollectionMetadata to test function it wraps")
def _(func=example_test):
    out_func = testable_test(func)

    assert out_func.ward_meta == CollectionMetadata(
        marker=None,
        description="testable test description",
        is_fixture=False,
        scope=Scope.Test,
        bound_args=None,
        path=FORCE_TEST_PATH,
    )


@test("@test doesn't attach CollectionMetadata to functions in non-test modules")
def _(func=example_test):
    func.__module__ = "blah"
    out_func = test("test")(func)

    assert not hasattr(out_func, "ward_meta")


@test("@test attaches CollectionMetadata to functions in modules ending in '_test'")
def _(func=example_test):
    func.__module__ = "its_a_test"
    out_func = test("test")(func)

    assert hasattr(out_func, "ward_meta")


@test("@test doesn't attach CollectionMetadata to tests from imported modules")
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


for outcome, should_fail_session in [
    (TestOutcome.PASS, False),
    (TestOutcome.FAIL, True),
    (TestOutcome.SKIP, False),
    (TestOutcome.XPASS, True),
    (TestOutcome.XFAIL, False),
    (TestOutcome.DRYRUN, False),
]:

    @test("{outcome}.will_fail_session is `{should_fail_session}`")
    def _(outcome=outcome, should_fail_session=should_fail_session):
        assert outcome.will_fail_session is should_fail_session

    @test("{outcome}.{will,wont}_fail_session are opposites")
    def _(outcome=outcome):
        assert outcome.will_fail_session is (not outcome.wont_fail_session)


@test("fixtures_used_directly_by_tests finds used fixture")
def _():
    @fixture
    def f():
        pass

    t = Test(lambda f=f: None, module_name="")

    assert fixtures_used_directly_by_tests([t]) == {Fixture(f): [t]}


@test("fixtures_used_directly_by_tests doesn't follow indirect dependencies")
def _():
    @fixture
    def parent():
        pass

    @fixture
    def child():
        pass

    t = Test(lambda c=child: None, module_name="")

    assert fixtures_used_directly_by_tests([t]) == {Fixture(child): [t]}


@test("fixtures_used_directly_by_tests works on a complex example")
def _():
    @fixture
    def parent():
        pass

    @fixture
    def child():
        pass

    @fixture
    def not_used():
        pass

    t1 = Test(lambda c=child: None, module_name="")
    t2 = Test(lambda p=parent, c=child: None, module_name="")
    t3 = Test(lambda _: None, module_name="")

    assert fixtures_used_directly_by_tests([t1, t2, t3]) == {
        Fixture(child): [t1, t2],
        Fixture(parent): [t2],
    }
