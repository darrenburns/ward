from ward import expect, fixture, test
from ward.fixtures import Fixture, FixtureCache


@fixture
def exception_raising_fixture():
    def i_raise_an_exception():
        raise ZeroDivisionError()

    return Fixture(fn=i_raise_an_exception)


@test("FixtureRegistry.cache_fixture can store and retrieve a single fixture")
def _(f=exception_raising_fixture):
    cache = FixtureCache()
    cache.cache_fixture(f)

    expect(cache[f.key]).equals(f)
