from python_tester import expect
from python_tester.fixtures import Fixture, FixtureExecutionError, FixtureRegistry


def test_fixture_resolve_resolves_tree_correctly():
    def grandchild_a():
        return 1

    def child_b():
        return 1

    def child_a(grandchild_a):
        return grandchild_a + 1

    def parent(child_a, child_b):
        return child_a + child_b + 1

    grandchild_a_fix = Fixture(name="grandchild_a", fn=grandchild_a)
    child_a_fix = Fixture(name="child_a", fn=child_a)
    child_b_fix = Fixture(name="child_b", fn=child_b)
    parent_fix = Fixture(name="fix_a", fn=parent)

    registry = FixtureRegistry()
    registry.cache_fixtures((grandchild_a_fix, child_a_fix, child_b_fix, parent_fix))

    resolved_parent = parent_fix.resolve(registry)

    # Each of the fixtures add 1, so the final value returned
    # by the tree should be 4, since there are 4 fixtures.
    assert resolved_parent == 4


def test_fixture_resolve_raises_FixtureExecutionError_when_fixture_cant_be_executed():
    def i_raise_an_exception():
        # A ZeroDivisionError is thrown by this fixture,
        # but we expect that this results in a FixtureExecutionError
        raise ZeroDivisionError()

    fix = Fixture(name="fix_a", fn=i_raise_an_exception)
    registry = FixtureRegistry()
    registry.cache_fixtures([fix])

    with expect.raises(FixtureExecutionError):
        fix.resolve(registry)
