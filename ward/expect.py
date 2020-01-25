from enum import Enum
from typing import Type, Any


class raises:
    def __init__(self, expected_ex_type: Type[Exception]):
        self.expected_ex_type = expected_ex_type

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not self.expected_ex_type:
            raise AssertionError(
                f"Expected exception {self.expected_ex_type}, but {exc_type} was raised instead."
            )
        return True


class Operator(Enum):
    Equals = "=="
    In = "in"


class TestFailure(Exception):
    def __init__(
        self,
        message: str,
        lhs: Any,
        rhs: Any,
        error_line: int,
        operator: Operator,
        assert_msg: str,
    ):
        self.lhs = lhs
        self.rhs = rhs
        self.message = message
        self.error_line = error_line
        self.operator = operator
        self.assert_msg = assert_msg
