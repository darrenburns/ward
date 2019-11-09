from ward import expect, fixture, test, Scope
from ward.fixtures import Fixture, FixtureCache


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
