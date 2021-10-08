import inspect

from ward import each, test, xfail
from ward.expect import (
    TestAssertionFailure,
    assert_equal,
    assert_greater_than,
    assert_greater_than_equal_to,
    assert_in,
    assert_is,
    assert_is_not,
    assert_less_than,
    assert_less_than_equal_to,
    assert_not_equal,
    assert_not_in,
    raises,
)


@test("correct error_line is set")
def _():
    assert_lineno = inspect.currentframe().f_lineno + 2
    with raises(TestAssertionFailure) as ctx:
        assert_equal(0, 1, "msg")
    assert ctx.raised.error_line == assert_lineno


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
        assert_is,
        assert_is_not,
    ),
    lhs=each(1, 1, "a", "a", 2, 2, 1, 1, "a", "a"),
    rhs=each(2, 1, "b", "a", 1, 1, 2, 2, "b", "a"),
):
    with raises(TestAssertionFailure):
        func(lhs, rhs, "")


@test("ward.raises raises AssertionError if the expected error is not raised")
def _():
    with raises(AssertionError):
        with raises(ValueError):
            raise RuntimeError


@test("ward.raises doesn't raise if the expected error is raised")
def _():
    with raises(ValueError):
        raise ValueError


@test("ward.raises doesn't raise if the a base class of the error is raised")
def _():
    class SubClass(ValueError):
        pass

    with raises(ValueError):
        raise SubClass()


@test("ward.raises gives access to the raised error afterwards")
def _():
    err = ValueError("x")
    with raises(ValueError) as ctx:
        raise err
    assert ctx.raised is err


@test("ward.raises allows to easily check the error message")
def _():
    with raises(ValueError) as ctx:
        raise ValueError("xyz")
    assert "y" in str(ctx.raised)


@test("ward.raises assertion error if no exception is raised")
@xfail
def _():
    with raises(ValueError):
        pass


@test("ward.raises.raised and try/except include a similar traceback")
def _():
    import traceback

    def raising():
        raise ValueError

    def dangerous():
        raising()

    try:
        dangerous()
    except ValueError as err:
        try_tb = traceback.extract_tb(err.__traceback__)

    with raises(ValueError) as ctx:
        dangerous()
    raises_tb = traceback.extract_tb(ctx.raised.__traceback__)

    assert try_tb[1:] == raises_tb[1:]
