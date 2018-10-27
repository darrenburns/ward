from python_tester.collect.fixtures import fixture


@fixture
def i_am_a_fixture(another_fixture):
    return "I AM A FIXTURE RETURN VALUE + " + str(another_fixture)


@fixture
def another_fixture():
    return 1234


@fixture
def some_other_fixture():
    return "hello"


def test_one_plus_two_equals_three(i_am_a_fixture, some_other_fixture):
    assert 1 + 2 == 4
