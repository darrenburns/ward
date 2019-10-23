from ward import expect, fixture, raises, test
from ward.fixtures import Fixture, FixtureExecutionError, FixtureRegistry


@fixture
def exception_raising_fixture():
    def i_raise_an_exception():
        raise ZeroDivisionError()

    return Fixture(key="fix_a", fn=i_raise_an_exception)


@test("Fixture.resolve correctly recurses fixture tree, collecting dependencies")
def _():
    def grandchild_a():
        return 1

    def child_b():
        return 1

    def child_a(grandchild_a):
        return grandchild_a + 1

    def parent(child_a, child_b):
        return child_a + child_b + 1

    grandchild_a_fix = Fixture(key="grandchild_a", fn=grandchild_a)
    child_a_fix = Fixture(key="child_a", fn=child_a)
    child_b_fix = Fixture(key="child_b", fn=child_b)
    parent_fix = Fixture(key="fix_a", fn=parent)

    registry = FixtureRegistry()
    registry.cache_fixtures((grandchild_a_fix, child_a_fix, child_b_fix, parent_fix))

    resolved_parent = parent_fix.resolve(registry)

    # Each of the fixtures add 1, so the final value returned
    # by the tree should be 4, since there are 4 fixtures.
    expect(resolved_parent.resolved_val).equals(4)


@test("FixtureRegistry.cache_fixture can store and retrieve a single fixture")
def _(exception_raising_fixture):
    registry = FixtureRegistry()
    registry.cache_fixture(exception_raising_fixture)

    expect(registry[exception_raising_fixture.key]).equals(exception_raising_fixture)


@test("FixtureRegistry.resolve raises FixtureExecutionError when fixture raises an exception")
def _(exception_raising_fixture):
    registry = FixtureRegistry()
    registry.cache_fixtures([exception_raising_fixture])

    with raises(FixtureExecutionError):
        exception_raising_fixture.resolve(registry)
