from parametrized import parametrized

from python_tester.collect.fixtures import fixture
from python_tester.collect.param import with_params


@fixture
def three(one, two):
    return one + two


@fixture
def two(one):
    return one + one


@fixture
def one():
    return 1


@with_params([
    ('param', 'another'),
    ('valueA', 'valueB'),
])
def test_one_plus_two_equals_threec(param, another, one, two, three):
    assert one + two + param == three + param

def test_one_plus_two_equals_three(one, two, three):
    assert one + two == three

def test_one_plus_two_equals_threea(one, two, three):
    assert one + two == 9

def test_one_plus_two_equals_threeb(one, two, three):
    assert one + two == three

def test_one_plus_two_equals_threed(one, two, three):
    assert one + two == three

def test_one_plus_two_equals_threee(one, two, three):
    assert one + two == three

def test_something_or_other(i_am_a_fixture):
    assert 1 + 1 == 2

def test_one_plus_two_equals_threef(one, two, three):
    assert one + two == three

def test_one_plus_two_equals_threei(one, two):
    assert one + two  == 3

def test_one_plus_two_equals_threeg(one, two, three):
    assert one + two == three

def test_one_plus_two_equals_threeh(one, two, three):
    assert one + two == three


def test_one_plus_two_equals_threej(one, two, three):
    assert one + two == three
