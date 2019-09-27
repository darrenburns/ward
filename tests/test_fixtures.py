from python_tester.fixtures import Fixture, FixtureRegistry


# Start constructing a tree of fixtures

def grandchild_a():
    return 1


def child_b():
    return 1


def child_a(grandchild_a):
    return grandchild_a + 1


def parent(child_a, child_b):
    return child_a + child_b + 1


# End constructing a tree of fixtures


def test_fixture_resolve_resolves_tree_correctly():
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
