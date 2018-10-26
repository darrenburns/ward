from python_tester.collect.fixtures import fixture


@fixture
def i_am_a_fixture():
    return "I AM A FIXTURE RETURN VALUE"


@fixture
def another_fixture():
    return 1234


def test_one_plus_two_equals_three():
    assert 1 + 2 == 4
