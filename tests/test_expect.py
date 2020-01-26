from ward import test, each
from ward.expect import assert_not_equal, TestFailure, raises, assert_equal, assert_in, assert_not_in


@test("{func.__name__}({lhs}, {rhs}) is None")
def _(
    func=each(assert_equal, assert_not_equal, assert_in, assert_not_in),
    lhs=each(1, 1, "a", "a"),
    rhs=each(1, 2, "a", "b"),
):
    assert func(lhs, rhs, "") is None


@test("{func.__name__}({lhs}, {rhs}) raises TestFailure")
def _(
    func=each(assert_equal, assert_not_equal, assert_in, assert_not_in),
    lhs=each(1, 1, "a", "a"),
    rhs=each(2, 1, "b", "a"),
):
    with raises(TestFailure):
        func(lhs, rhs, "")
