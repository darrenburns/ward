from typing import List

from tests.test_suite import testable_test
from ward import expect, fixture, test, Scope
from ward.fixtures import Fixture, FixtureCache, using
from ward.testing import Test


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

    expect(cache.get(f.key, Scope.Test, "test_id")).equals(f)


@fixture
def recorded_events():
    return []


@fixture
def global_fixture(events=recorded_events):
    @fixture(scope=Scope.Global)
    def g():
        yield "g"
        events.append("teardown g")

    return g


@fixture
def module_fixture(events=recorded_events):
    @fixture(scope=Scope.Module)
    def m():
        yield "m"
        events.append("teardown m")

    return m


@fixture
def default_fixture(events=recorded_events):
    @fixture
    def t():
        yield "t"
        events.append("teardown t")

    return t


@fixture
def my_test(
    f1=exception_raising_fixture,
    f2=global_fixture,
    f3=module_fixture,
    f4=default_fixture,
):
    # Inject these fixtures into a test, and resolve them
    # to ensure they're ready to be torn down.
    @testable_test
    def t(f1=f1, f2=f2, f3=f3, f4=f4):
        pass

    return Test(t, "")


@fixture
def cache(t=my_test):
    c = FixtureCache()
    t.resolve_args(c)
    return c


@test("FixtureCache.get_fixtures_at_scope correct for Scope.Test")
def _(cache: FixtureCache = cache, t: Test = my_test, default_fixture=default_fixture):
    fixtures_at_scope = cache.get_fixtures_at_scope(Scope.Test, t.id)

    fixture = list(fixtures_at_scope.values())[0]

    expect(fixtures_at_scope).has_length(1)
    expect(fixture.fn).equals(default_fixture)


@test("FixtureCache.get_fixtures_at_scope correct for Scope.Module")
def _(cache: FixtureCache = cache, module_fixture=module_fixture):
    fixtures_at_scope = cache.get_fixtures_at_scope(Scope.Module, testable_test.path)

    fixture = list(fixtures_at_scope.values())[0]

    expect(fixtures_at_scope).has_length(1)
    expect(fixture.fn).equals(module_fixture)


@test("FixtureCache.get_fixtures_at_scope correct for Scope.Global")
def _(cache: FixtureCache = cache, global_fixture=global_fixture):
    fixtures_at_scope = cache.get_fixtures_at_scope(Scope.Global, Scope.Global)

    fixture = list(fixtures_at_scope.values())[0]

    expect(fixtures_at_scope).has_length(1)
    expect(fixture.fn).equals(global_fixture)


@test("FixtureCache.teardown_fixtures_for_scope removes Test fixtures from cache")
def _(cache: FixtureCache = cache, t: Test = my_test):
    cache.teardown_fixtures_for_scope(Scope.Test, t.id)

    fixtures_at_scope = cache.get_fixtures_at_scope(Scope.Test, t.id)

    expect(fixtures_at_scope).equals({})


@test("FixtureCache.teardown_fixtures_for_scope runs teardown for Test fixtures")
def _(cache: FixtureCache = cache, t: Test = my_test, events: List = recorded_events):
    cache.teardown_fixtures_for_scope(Scope.Test, t.id)

    expect(events).equals(["teardown t"])


@test("FixtureCache.teardown_fixtures_for_scope removes Module fixtures from cache")
def _(cache: FixtureCache = cache,):
    cache.teardown_fixtures_for_scope(Scope.Module, testable_test.path)

    fixtures_at_scope = cache.get_fixtures_at_scope(Scope.Module, testable_test.path)

    expect(fixtures_at_scope).equals({})


@test("FixtureCache.teardown_fixtures_for_scope runs teardown for Module fixtures")
def _(cache: FixtureCache = cache, events: List = recorded_events):
    cache.teardown_fixtures_for_scope(Scope.Module, testable_test.path)

    expect(events).equals(["teardown m"])


@test("FixtureCache.teardown_global_fixtures removes Global fixtures from cache")
def _(cache: FixtureCache = cache,):
    cache.teardown_global_fixtures()

    fixtures_at_scope = cache.get_fixtures_at_scope(Scope.Global, Scope.Global)

    expect(fixtures_at_scope).equals({})


@test("FixtureCache.teardown_global_fixtures runs teardown of all Global fixtures")
def _(cache: FixtureCache = cache, events: List = recorded_events):
    cache.teardown_global_fixtures()

    expect(events).equals(["teardown g"])


@test("using decorator sets bound args correctly")
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

    expect(bound_args.arguments).equals(expected)
