from python_tester.collect.fixtures import fixture


@fixture
def three(one, two):
    return one + two


@fixture
def two(one):
    return one + one


@fixture
def one():
    return 1


def test_one_plus_two_equals_three(one, two, three):
    assert one + two == three
