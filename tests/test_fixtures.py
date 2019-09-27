from python_tester import expect
from python_tester.fixtures import Fixture, FixtureExecutionError, FixtureRegistry, fixture


@fixture
def exception_raising_fixture():
    def i_raise_an_exception():
        raise ZeroDivisionError()

    return Fixture(key="fix_a", fn=i_raise_an_exception)


def test_fixture_resolve_resolves_tree_correctly():
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
    assert resolved_parent == 4


def test_fixture_registry_cache_fixture(exception_raising_fixture):
    registry = FixtureRegistry()
    registry.cache_fixture(exception_raising_fixture)

    assert registry[exception_raising_fixture.name] == exception_raising_fixture


def test_fixture_resolve_raises_FixtureExecutionError_when_fixture_cant_be_executed(
    exception_raising_fixture
):
    registry = FixtureRegistry()
    registry.cache_fixtures([exception_raising_fixture])

    with expect.raises(FixtureExecutionError):
        exception_raising_fixture.resolve(registry)
