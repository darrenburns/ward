import inspect
import types
from dataclasses import dataclass
from enum import Enum
from typing import Any, ContextManager, Generic, Optional, Type, TypeVar, cast

__all__ = [
    "raises",
    "assert_equal",
    "assert_not_equal",
    "assert_in",
    "assert_not_in",
    "assert_is",
    "assert_is_not",
    "assert_less_than",
    "assert_less_than_equal_to",
    "assert_greater_than",
    "assert_greater_than_equal_to",
]

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


@dataclass
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


def assert_equal(lhs_val: Any, rhs_val: Any, assert_msg: str) -> None:
    """
    Check whether two objects are equal. Raises a ``TestFailure`` if not.
    Args:
        lhs_val: The value on the left side of ``==``
        rhs_val: The value on the right side of ``==``
        assert_msg: The assertion message from the ``assert`` statement

    Returns: None
    Raises: TestFailure
    """
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


def assert_not_equal(lhs_val: Any, rhs_val: Any, assert_msg: str) -> None:
    """
    Check whether two objects are not equal to each other. Raises a ``TestFailure`` if not.

    Args:
        lhs_val: The value on the left side of ``!=``
        rhs_val: The value on the right side of ``!=``
        assert_msg: The assertion message from the ``assert`` statement

    Returns: None
    Raises: TestFailure
    """
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


def assert_in(lhs_val: Any, rhs_val: Any, assert_msg: str) -> None:
    """
    Check if an object is contained within another via ``lhs_val in rhs_val``. Raises ``TestFailure`` if not.

    Args:
        lhs_val: The value on the left side of ``in``
        rhs_val: The value on the right side of ``in``
        assert_msg: The assertion message from the ``assert`` statement

    Returns: None
    Raises: TestFailure
    """
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


def assert_not_in(lhs_val: Any, rhs_val: Any, assert_msg: str) -> None:
    """
    Check if an object is not contained within another via ``lhs_val not in rhs_val``.
    Raises ``TestFailure`` if lhs is contained within rhs.

    Args:
        lhs_val: The value on the left side of ``not in``
        rhs_val: The value on the right side of ``not in``
        assert_msg: The assertion message from the ``assert`` statement

    Returns: None
    Raises: TestFailure
    """
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


def assert_is(lhs_val: Any, rhs_val: Any, assert_msg: str) -> None:
    """
    Check the object identity via ``lhs_val is rhs_val``. Raises ``TestFailure`` if not identical.

    Args:
        lhs_val: The value on the left side of ``is``
        rhs_val: The value on the right side of ``is``
        assert_msg: The assertion message from the ``assert`` statement

    Returns: None
    Raises: TestFailure
    """
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


def assert_is_not(lhs_val: Any, rhs_val: Any, assert_msg: str) -> None:
    """
    Check the object identity via ``lhs_val is not rhs_val``. Raises ``TestFailure`` if identical.

    Args:
        lhs_val: The value on the left side of ``is not``
        rhs_val: The value on the right side of ``is not``
        assert_msg: The assertion message from the ``assert`` statement

    Returns: None
    Raises: TestFailure
    """
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


def assert_less_than(lhs_val: Any, rhs_val: Any, assert_msg: str) -> None:
    """
    Check lhs_val is less than the rhs_val via ``lhs_val < rhs_val``. Raises ``TestFailure`` if not.

    Args:
        lhs_val: The value on the left side of ``<``
        rhs_val: The value on the right side of ``<``
        assert_msg: The assertion message from the ``assert`` statement

    Returns: None
    Raises: TestFailure
    """
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


def assert_less_than_equal_to(lhs_val: Any, rhs_val: Any, assert_msg: str) -> None:
    """
    Check lhs_val is less than or equal to the rhs_val via ``lhs_val <= rhs_val``. Raises ``TestFailure`` if not.

    Args:
        lhs_val: The value on the left side of ``<=``
        rhs_val: The value on the right side of ``<=``
        assert_msg: The assertion message from the ``assert`` statement

    Returns: None
    Raises: TestFailure
    """
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


def assert_greater_than(lhs_val: Any, rhs_val: Any, assert_msg: str) -> None:
    """
    Check lhs_val is greater than the rhs_val via ``lhs_val > rhs_val``. Raises ``TestFailure`` if not.

    Args:
        lhs_val: The value on the left side of ``>``
        rhs_val: The value on the right side of ``>``
        assert_msg: The assertion message from the ``assert`` statement

    Returns: None
    Raises: TestFailure
    """
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


def assert_greater_than_equal_to(lhs_val: Any, rhs_val: Any, assert_msg: str) -> None:
    """
    Check lhs_val is greater than or equal to the rhs_val via ``lhs_val >= rhs_val``. Raises ``TestFailure`` if not.

    Args:
        lhs_val: The value on the left side of ``>=``
        rhs_val: The value on the right side of ``>=``
        assert_msg: The assertion message from the ``assert`` statement

    Returns: None
    Raises: TestFailure
    """
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
