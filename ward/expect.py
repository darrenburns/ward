import functools
from dataclasses import dataclass
from typing import Type, Any, List


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


@dataclass
class Expected:
    this: Any
    op: str
    that: Any
    success: bool = True


class ExpectationFailed(Exception):
    def __init__(self, message: str, history: List[Expected]):
        self.message = message
        self.history = history


def record_expect_in_history(func):
    @functools.wraps(func)
    def wrapped_func(self, that: Any, *args, **kwargs) -> "expect":
        rv = func(self, that, *args, **kwargs)
        if rv:
            self.history.append(Expected(this=self.this, op=func.__name__, that=that, success=True))
            return self
        else:
            self.history.append(Expected(this=self.this, op=func.__name__, that=that, success=False))
            raise ExpectationFailed(f"{func.__name__} expectation failed", self.history)

    return wrapped_func


class expect:
    def __init__(self, this: Any):
        self.this = this
        self.history: List[Expected] = []

    @record_expect_in_history
    def equals(self, that: Any):
        return self.this == that

    @record_expect_in_history
    def is_less_than(self, that: Any):
        return self.this < that

    @record_expect_in_history
    def is_greater_than(self, that: Any):
        return self.this > that

    @record_expect_in_history
    def contains(self, that: Any):
        return that in self.this

    @record_expect_in_history
    def is_the_same_as(self, that: Any):
        return self.this is that
