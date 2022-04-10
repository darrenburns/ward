import sys
from typing import List

from tests.utilities import dummy_fixture, testable_test
from ward import each, fixture, raises, test
from ward._errors import FixtureError
from ward._fixtures import FixtureCache, fixture_parents_and_children, is_fixture
from ward.fixtures import Fixture, TeardownResult, using
from ward.models import Scope
from ward.testing import Test, xfail


@fixture
def exception_raising_fixture():
    @fixture
    def i_raise_an_exception():
        raise ZeroDivisionError()

    return Fixture(fn=i_raise_an_exception)


@test("FixtureCache.cache_fixture caches a single fixture")
def _(f=exception_raising_fixture):
    cache = FixtureCache()
    cache.cache_fixture(f, "test_id")

    assert cache.get(f.key, Scope.Test, "test_id") == f


@fixture
def recorded_events():
    return []


@fixture
def global_fixture(events=recorded_events):
    @fixture(scope=Scope.Global)
    def g():
        yield "g"
        print("stdout")
        sys.stderr.write("stderr")
        events.append("teardown g")

    return g


@fixture
def module_fixture(events=recorded_events):
    @fixture(scope=Scope.Module)
    def m():
        yield "m"
        print("stdout")
        sys.stderr.write("stderr")
        events.append("teardown m")

    return m


@fixture
def default_fixture(events=recorded_events):
    @fixture
    def t():
        yield "t"
        print("stdout")
        sys.stderr.write("stderr")
        events.append("teardown t")

    return t


@fixture
def my_test(
    f1=exception_raising_fixture,
    f2=global_fixture,
    f3=module_fixture,
    f4=default_fixture,
):
    """
    Inject these fixtures into a test, and resolve them
    to ensure they're ready to be torn down.
    """

    @testable_test
    def t(f1=f1, f2=f2, f3=f3, f4=f4):
        pass

    return Test(t, "")


@fixture
def cache(t=my_test):
    c = FixtureCache()
    t.resolver.resolve_args(c)
    return c


@test("FixtureCache.get_fixtures_at_scope correct for Scope.Test")
def _(cache: FixtureCache = cache, t: Test = my_test, default_fixture=default_fixture):
    fixtures_at_scope = cache.get_fixtures_at_scope(Scope.Test, t.id)

    fixture = list(fixtures_at_scope.values())[0]

    assert len(fixtures_at_scope) == 1
    assert fixture.fn == default_fixture


@test("FixtureCache.get_fixtures_at_scope correct for Scope.Module")
def _(cache: FixtureCache = cache, module_fixture=module_fixture):
    fixtures_at_scope = cache.get_fixtures_at_scope(Scope.Module, testable_test.path)  # type: ignore[attr-defined]

    fixture = list(fixtures_at_scope.values())[0]

    assert len(fixtures_at_scope) == 1
    assert fixture.fn == module_fixture


@test("FixtureCache.get_fixtures_at_scope correct for Scope.Global")
def _(cache: FixtureCache = cache, global_fixture=global_fixture):
    fixtures_at_scope = cache.get_fixtures_at_scope(Scope.Global, Scope.Global)

    fixture = list(fixtures_at_scope.values())[0]

    assert len(fixtures_at_scope) == 1
    assert fixture.fn == global_fixture


@test("FixtureCache.teardown_fixtures_for_scope removes Test fixtures from cache")
def _(cache: FixtureCache = cache, t: Test = my_test):
    cache.teardown_fixtures_for_scope(Scope.Test, t.id, capture_output=True)

    fixtures_at_scope = cache.get_fixtures_at_scope(Scope.Test, t.id)

    assert fixtures_at_scope == {}


@test("FixtureCache.teardown_fixtures_for_scope runs teardown for Test fixtures")
def _(cache: FixtureCache = cache, t: Test = my_test, events: List = recorded_events):
    cache.teardown_fixtures_for_scope(Scope.Test, t.id, capture_output=False)

    assert events == ["teardown t"]


@test(
    "FixtureCache.teardown_fixtures_for_scope captures exceptions that occur in teardown code"
)
def _():
    error = ZeroDivisionError("oh no")

    @fixture
    def raises_in_teardown():
        yield "a"
        print("stdout")
        sys.stderr.write("stderr")
        raise error

    @testable_test
    def t(fix=raises_in_teardown):
        pass

    cache = FixtureCache()
    t = Test(t, "")
    t.resolver.resolve_args(cache)

    teardown_results: List[TeardownResult] = cache.teardown_fixtures_for_scope(
        scope=Scope.Test, scope_key=t.id, capture_output=True
    )

    assert len(teardown_results) == 1
    assert teardown_results[0].captured_exception == error
    # Ensure that we still capture stdout, stderr on exception
    assert teardown_results[0].sout == "stdout\n"
    assert teardown_results[0].serr == "stderr"


@xfail(reason="Known issue")
@test(
    "FixtureCache.teardown_fixtures_for_scope captures StopIteration that occur in teardown code"
)
def _():
    error = StopIteration("oh no")

    @fixture
    def raises_in_teardown():
        yield "a"
        print("stdout")
        sys.stderr.write("stderr")
        raise error

    @testable_test
    def t(fix=raises_in_teardown):
        pass

    cache = FixtureCache()
    t = Test(t, "")
    t.resolver.resolve_args(cache)

    teardown_results: List[TeardownResult] = cache.teardown_fixtures_for_scope(
        scope=Scope.Test, scope_key=t.id, capture_output=True
    )

    assert len(teardown_results) == 1
    assert teardown_results[0].captured_exception == error
    # Ensure that we still capture stdout, stderr on exception
    assert teardown_results[0].sout == "stdout\n"
    assert teardown_results[0].serr == "stderr"


@test(
    "FixtureCache.teardown_fixtures_for_scope captures output from test-scoped teardown code"
)
def _(cache: FixtureCache = cache, t: Test = my_test):
    teardown_results: List[TeardownResult] = cache.teardown_fixtures_for_scope(
        Scope.Test, t.id, capture_output=True
    )

    # There are 4 fixtures injected into the test. Only 2 are test-scoped, and teardown
    # code only runs in 1 of those.
    assert len(teardown_results) == 1
    assert teardown_results[0].captured_exception is None
    assert teardown_results[0].sout == "stdout\n"
    assert teardown_results[0].serr == "stderr"


@test("FixtureCache.teardown_fixtures_for_scope removes Module fixtures from cache")
def _(cache: FixtureCache = cache):
    cache.teardown_fixtures_for_scope(
        Scope.Module, testable_test.path, capture_output=True  # type: ignore[attr-defined]
    )

    fixtures_at_scope = cache.get_fixtures_at_scope(Scope.Module, testable_test.path)  # type: ignore[attr-defined]

    assert fixtures_at_scope == {}


@test("FixtureCache.teardown_fixtures_for_scope runs teardown for Module fixtures")
def _(cache: FixtureCache = cache, events: List = recorded_events):
    cache.teardown_fixtures_for_scope(
        Scope.Module, testable_test.path, capture_output=False  # type: ignore[attr-defined]
    )

    assert events == ["teardown m"]


@test(
    "FixtureCache.teardown_fixtures_for_scope captures output from Module fixture teardown code"
)
def _(cache: FixtureCache = cache):
    teardown_results = cache.teardown_fixtures_for_scope(
        Scope.Module, testable_test.path, capture_output=True  # type: ignore[attr-defined]
    )

    assert len(teardown_results) == 1
    assert teardown_results[0].sout == "stdout\n"
    assert teardown_results[0].serr == "stderr"


@test("FixtureCache.teardown_global_fixtures removes Global fixtures from cache")
def _(cache: FixtureCache = cache):
    cache.teardown_global_fixtures(capture_output=True)

    fixtures_at_scope = cache.get_fixtures_at_scope(Scope.Global, Scope.Global)

    assert fixtures_at_scope == {}


@test("FixtureCache.teardown_global_fixtures runs teardown of all Global fixtures")
def _(cache: FixtureCache = cache, events: List = recorded_events):
    cache.teardown_global_fixtures(capture_output=False)

    assert events == ["teardown g"]


@test(
    "FixtureCache.teardown_global_fixtures captures stdout and stderr from teardown code"
)
def _(cache: FixtureCache = cache):
    teardown_results = cache.teardown_global_fixtures(capture_output=True)

    # The cache contains a single global resolved fixture, which writes to sout/serr during teardown
    assert len(teardown_results) == 1
    assert teardown_results[0].sout == "stdout\n"
    assert teardown_results[0].serr == "stderr"


@test("the `@using` decorator sets bound args correctly")
def _():
    @fixture
    def fixture_a():
        pass

    @testable_test
    @using(a=fixture_a, b="val")
    def t(a, b):
        pass

    bound_args = t.ward_meta.bound_args
    expected = {"a": fixture_a, "b": "val"}

    assert bound_args.arguments == expected


@test("resolving a fixture that exits {exit_code} raises a FixtureError")
def _(exit_code=each(0, 1)):
    @fixture
    def exits():
        sys.exit(exit_code)

    t = Test(fn=lambda exits=exits: None, module_name="foo")

    with raises(FixtureError):
        t.resolver.resolve_args(FixtureCache())


@test("is_fixture returns True for fixtures")
def _():
    # I would have liked to combine this test into the parameterised test below,
    # but if we put the fixture in the each, it would get resolved!
    # So we need to check it from global scope.
    assert is_fixture(dummy_fixture)


@test("arg_is_fixture returns False for not-fixtures ({not_fixture!r})")
def _(not_fixture=each("foo", 5, is_fixture, Fixture)):
    assert not is_fixture(not_fixture)


@test("Fixture.parents returns the parents of the fixture as Fixture instances")
def _():
    @fixture
    def parent_a():
        pass

    @fixture
    def parent_b():
        pass

    @fixture
    def child(a=parent_a, b=parent_b):
        pass

    assert Fixture(child).parents() == [Fixture(parent_a), Fixture(parent_b)]


@test("Fixture.parents returns an empty collection if the fixture has no parents")
def _():
    @fixture
    def fix():
        pass

    assert len(Fixture(fix).parents()) == 0


@test("fixture_parents_and_children analyzes fixture dependencies correctly")
def _():
    @fixture
    def a():
        pass

    @fixture
    def b():
        pass

    @fixture
    def c(a=a, b=b):
        pass

    @fixture
    def d(a=a, c=c):
        pass

    fa, fb, fc, fd = fixtures = [Fixture(f) for f in (a, b, c, d)]

    to_parents, to_children = fixture_parents_and_children(fixtures)

    assert to_parents == {fa: [], fb: [], fc: [fa, fb], fd: [fa, fc]}

    assert to_children == {
        fa: [fc, fd],
        fb: [fc],
        fc: [fd],
        fd: [],
    }
