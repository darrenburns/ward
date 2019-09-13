from parameterized import parameterized

from python_tester.collect.fixtures import fixture


@fixture
def something_three():
    return "three"


@parameterized.expand([
    (1, 1, 2),
    (2, 2, 4),
    (3, 3, 6),
])
def test_something_or_other(a, b, c):
    assert a + b == c
