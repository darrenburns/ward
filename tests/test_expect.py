from ward import test, each
from ward.expect import (
    assert_not_equal,
    TestFailure,
    raises,
    assert_equal,
    assert_in,
    assert_not_in,
    assert_is_not,
    assert_is,
    assert_less_than,
    assert_less_than_equal_to,
    assert_greater_than_equal_to,
    assert_greater_than,
)


@test("{func.__name__}({lhs}, {rhs}) is None")
def _(
    func=each(
        assert_equal,
        assert_not_equal,
        assert_in,
        assert_not_in,
        assert_is,
        assert_is_not,
        assert_less_than,
        assert_less_than_equal_to,
        assert_less_than_equal_to,
        assert_greater_than,
        assert_greater_than_equal_to,
        assert_greater_than_equal_to,
    ),
    lhs=each(1, 1, "a", "a", ..., True, 1, 1, 1, 2, 2, 1),
    rhs=each(1, 2, "a", "b", ..., None, 2, 2, 1, 1, 1, 1),
):
    assert func(lhs, rhs, "") is None


@test("{func.__name__}({lhs}, {rhs}) raises TestFailure")
def _(
    func=each(
        assert_equal,
        assert_not_equal,
        assert_in,
        assert_not_in,
        assert_less_than,
        assert_less_than_equal_to,
        assert_greater_than,
        assert_greater_than_equal_to,
    ),
    lhs=each(1, 1, "a", "a", 2, 2, 1, 1),
    rhs=each(2, 1, "b", "a", 1, 1, 2, 2),
):
    with raises(TestFailure):
        func(lhs, rhs, "")
