import functools
import math
from dataclasses import dataclass
from typing import Type, Any, List, Callable, Dict, Tuple


class raises:
    def __init__(self, expected_ex_type: Type[Exception]):
        self.expected_ex_type = expected_ex_type

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not self.expected_ex_type:
            raise AssertionError(f"Expected exception {self.expected_ex_type}, but {exc_type} was raised instead.")
        return True


@dataclass
class Expected:
    this: Any
    op: str
    that: Any
    op_args: Tuple
    op_kwargs: Dict
    success: bool = True


class ExpectationFailed(Exception):
    def __init__(self, message: str, history: List[Expected]):
        self.message = message
        self.history = history


def record_and_handle_outcome(func):
    @functools.wraps(func)
    def wrapped_func(self, that: Any, *args, **kwargs) -> "expect":
        rv = func(self, that, *args, **kwargs)
        if rv:
            self.history.append(
                Expected(this=self.this, op=func.__name__, that=that, success=True, op_args=args, op_kwargs=kwargs)
            )
            return self
        else:
            self.history.append(
                Expected(this=self.this, op=func.__name__, that=that, success=False, op_args=args, op_kwargs=kwargs)
            )
            raise ExpectationFailed(f"{func.__name__} expectation failed", self.history)

    return wrapped_func


class expect:
    def __init__(self, this: Any):
        self.this = this
        self.history: List[Expected] = []

    @record_and_handle_outcome
    def equals(self, that: Any):
        return self.this == that

    def not_equals(self, that: Any):
        return not self.equals(that)

    @record_and_handle_outcome
    def less_than(self, that: Any):
        return self.this < that

    def not_less_than(self, that: Any):
        return not self.less_than(that)

    @record_and_handle_outcome
    def less_than_or_equals(self, that: Any):
        return self.this <= that

    def not_less_than_or_equals(self, that: Any):
        return self.less_than_or_equals(that)

    @record_and_handle_outcome
    def greater_than(self, that: Any):
        return self.this > that

    def not_greater_than(self, that: Any):
        return not self.greater_than(that)

    @record_and_handle_outcome
    def greater_than_or_equals(self, that: Any):
        return self.this >= that

    def not_greater_than_or_equals(self, that: Any):
        return not self.greater_than_or_equals(that)

    @record_and_handle_outcome
    def contains(self, that: Any):
        return that in self.this

    def not_contains(self, that: Any):
        return not self.contains(that)

    @record_and_handle_outcome
    def has_length(self, length: int):
        return len(self.this) == length

    def not_has_length(self, length: int):
        return not self.has_length(length)

    @record_and_handle_outcome
    def instance_of(self, type: Type):
        return isinstance(self.this, type)

    def not_instance_of(self, type: Type):
        return not self.instance_of(type)

    @record_and_handle_outcome
    def satisfies(self, predicate: Callable[["expect"], bool]):
        return predicate(self.this)

    def not_satisfies(self, predicate: Callable[["expect"], bool]):
        return not self.satisfies(predicate)

    @record_and_handle_outcome
    def identical_to(self, that: Any):
        return self.this is that

    def not_identical_to(self, that: Any):
        return not self.identical_to(that)

    @record_and_handle_outcome
    def approx(self, that: Any, rel_tol: float = 1e-9, abs_tol: float = 0.0):
        return math.isclose(self.this, that, abs_tol=abs_tol, rel_tol=rel_tol)

    def not_approx(self, that: Any, rel_tol: float = 1e-9, abs_tol: float = 0.0):
        return not self.approx(that, rel_tol=rel_tol, abs_tol=abs_tol)

    @record_and_handle_outcome
    def called(self):
        return self.this.called

    def not_called(self):
        return not self.called

    @record_and_handle_outcome
    def called_once_with(self, *args, **kwargs):
        try:
            self.this.assert_called_once_with(*args, **kwargs)
        except AssertionError:
            return False
        return True

    def not_called_once_with(self, *args, **kwargs):
        return not self.called_once_with(*args, **kwargs)

    @record_and_handle_outcome
    def called_with(self, *args, **kwargs):
        try:
            self.this.assert_called_with(*args, **kwargs)
        except AssertionError:
            return False
        return True

    def not_called_with(self, *args, **kwargs):
        return not self.called_with(*args, **kwargs)
