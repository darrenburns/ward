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

def test_one_plus_two_equals_threea(one, two, three):
    assert one + two == three

def test_one_plus_two_equals_threeb(one, two, three):
    assert one + two == three

def test_one_plus_two_equals_threec(one, two, three):
    assert one + two == three

def test_one_plus_two_equals_threed(one, two, three):
    assert one + two == three

def test_one_plus_two_equals_threee(one, two, three):
    assert one + two == three

def test_one_plus_two_equals_threef(one, two, three):
    assert one + two == three

def test_one_plus_two_equals_threeg(one, two, three):
    assert one + two == three

def test_one_plus_two_equals_threeh(one, two, three):
    assert one + two == three

def test_one_plus_two_equals_three_ERROR(one, two):
    assert one + two == 9

def test_one_plus_two_equals_threej(one, two, three):
    assert one + two == three
