from python_tester.collect.fixtures import fixture


@fixture
def something_three():
    return "three"


def test_something_or_other(i_am_a_fixture):
    assert 1 + 1 == 2
