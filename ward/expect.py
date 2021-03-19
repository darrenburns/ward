import inspect
import types
from enum import Enum
from typing import Type, Any, ContextManager, TypeVar, Generic, Optional, cast

_E = TypeVar("_E", bound=Exception)


class raises(Generic[_E], ContextManager["raises[_E]"]):
    raised: _E

    def __init__(self, expected_ex_type: Type[_E]):
        self.expected_ex_type = expected_ex_type

    def __enter__(self) -> "raises[_E]":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[types.TracebackType],
    ) -> bool:
        if exc_type is not self.expected_ex_type:
            raise AssertionError(
                f"Expected exception {self.expected_ex_type}, but {exc_type} was raised instead."
            )
        self.raised: _E = cast(_E, exc_val)
        return True


class Comparison(Enum):
    Equals = "=="
    NotEquals = "!="
    In = "in"
    NotIn = "not in"
    Is = "is"
    IsNot = "is not"
    LessThan = "<"
    LessThanEqualTo = "<="
    GreaterThan = ">"
    GreaterThanEqualTo = ">="


class TestFailure(Exception):
    def __init__(
        self,
        message: str,
        lhs: Any,
        rhs: Any,
        error_line: int,
        operator: Comparison,
        assert_msg: str,
    ):
        self.lhs = lhs
        self.rhs = rhs
        self.message = message
        self.error_line = error_line
        self.operator = operator
        self.assert_msg = assert_msg


def assert_equal(lhs_val, rhs_val, assert_msg):
    if lhs_val != rhs_val:
        error_line_no = inspect.currentframe().f_back.f_lineno
        raise TestFailure(
            f"{lhs_val} does not equal {rhs_val}",
            lhs=lhs_val,
            rhs=rhs_val,
            error_line=error_line_no,
            operator=Comparison.Equals,
            assert_msg=assert_msg,
        )


def assert_not_equal(lhs_val, rhs_val, assert_msg):
    if lhs_val == rhs_val:
        error_line_no = inspect.currentframe().f_back.f_lineno
        raise TestFailure(
            f"{lhs_val} does equal {rhs_val}",
            lhs=lhs_val,
            rhs=rhs_val,
            error_line=error_line_no,
            operator=Comparison.NotEquals,
            assert_msg=assert_msg,
        )


def assert_in(lhs_val, rhs_val, assert_msg):
    if lhs_val not in rhs_val:
        error_line_no = inspect.currentframe().f_back.f_lineno
        raise TestFailure(
            f"{lhs_val} is not in {rhs_val}",
            lhs=lhs_val,
            rhs=rhs_val,
            error_line=error_line_no,
            operator=Comparison.In,
            assert_msg=assert_msg,
        )


def assert_not_in(lhs_val, rhs_val, assert_msg):
    if lhs_val in rhs_val:
        error_line_no = inspect.currentframe().f_back.f_lineno
        raise TestFailure(
            f"{lhs_val} is in {rhs_val}",
            lhs=lhs_val,
            rhs=rhs_val,
            error_line=error_line_no,
            operator=Comparison.NotIn,
            assert_msg=assert_msg,
        )


def assert_is(lhs_val, rhs_val, assert_msg):
    if lhs_val is not rhs_val:
        error_line_no = inspect.currentframe().f_back.f_lineno
        raise TestFailure(
            f"{lhs_val} is not {rhs_val}",
            lhs=lhs_val,
            rhs=rhs_val,
            error_line=error_line_no,
            operator=Comparison.Is,
            assert_msg=assert_msg,
        )


def assert_is_not(lhs_val, rhs_val, assert_msg):
    if lhs_val is rhs_val:
        error_line_no = inspect.currentframe().f_back.f_lineno
        raise TestFailure(
            f"{lhs_val} is {rhs_val}",
            lhs=lhs_val,
            rhs=rhs_val,
            error_line=error_line_no,
            operator=Comparison.IsNot,
            assert_msg=assert_msg,
        )


def assert_less_than(lhs_val, rhs_val, assert_msg):
    if lhs_val >= rhs_val:
        error_line_no = inspect.currentframe().f_back.f_lineno
        raise TestFailure(
            f"{lhs_val} >= {rhs_val}",
            lhs=lhs_val,
            rhs=rhs_val,
            error_line=error_line_no,
            operator=Comparison.LessThan,
            assert_msg=assert_msg,
        )


def assert_less_than_equal_to(lhs_val, rhs_val, assert_msg):
    if lhs_val > rhs_val:
        error_line_no = inspect.currentframe().f_back.f_lineno
        raise TestFailure(
            f"{lhs_val} > {rhs_val}",
            lhs=lhs_val,
            rhs=rhs_val,
            error_line=error_line_no,
            operator=Comparison.LessThanEqualTo,
            assert_msg=assert_msg,
        )


def assert_greater_than(lhs_val, rhs_val, assert_msg):
    if lhs_val <= rhs_val:
        error_line_no = inspect.currentframe().f_back.f_lineno
        raise TestFailure(
            f"{lhs_val} <= {rhs_val}",
            lhs=lhs_val,
            rhs=rhs_val,
            error_line=error_line_no,
            operator=Comparison.GreaterThan,
            assert_msg=assert_msg,
        )


def assert_greater_than_equal_to(lhs_val, rhs_val, assert_msg):
    if lhs_val < rhs_val:
        error_line_no = inspect.currentframe().f_back.f_lineno
        raise TestFailure(
            f"{lhs_val} < {rhs_val}",
            lhs=lhs_val,
            rhs=rhs_val,
            error_line=error_line_no,
            operator=Comparison.GreaterThanEqualTo,
            assert_msg=assert_msg,
        )
