import inspect
import math
from dataclasses import dataclass
from typing import Type, Any, List, Callable, Dict, Tuple, Optional, Iterable
from unittest.mock import _Call


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
    that: Optional[Any]
    op_args: Tuple
    op_kwargs: Dict
    success: bool = True


class ExpectationFailed(Exception):
    def __init__(self, message: str, history: List[Expected]):
        self.message = message
        self.history = history


class expect:
    def __init__(self, this: Any):
        self.this = this
        self.history: List[Expected] = []

    def equals(self, expected: Any):
        return self._handle_expect(self.this == expected, that=expected)

    def not_equals(self, that: Any):
        return self._handle_expect(self.this != that, that=that)

    def less_than(self, that: Any):
        return self._handle_expect(self.this < that, that=that)

    def not_less_than(self, that: Any):
        return self._handle_expect(not self.this < that, that=that)

    def less_than_or_equals(self, that: Any):
        return self._handle_expect(self.this <= that, that=that)

    def not_less_than_or_equals(self, that: Any):
        return self._handle_expect(not self.this <= that, that=that)

    def greater_than(self, that: Any):
        return self._handle_expect(self.this > that, that=that)

    def not_greater_than(self, that: Any):
        return self._handle_expect(not self.this > that, that=that)

    def greater_than_or_equals(self, that: Any):
        return self._handle_expect(self.this >= that, that=that)

    def not_greater_than_or_equals(self, that: Any):
        return self._handle_expect(not self.this >= that, that=that)

    def contains(self, that: Any):
        return self._handle_expect(that in self.this, that=that)

    def not_contains(self, that: Any):
        return self._handle_expect(that not in self.this, that=that)

    def contained_in(self, that: Iterable[Any]):
        return self._handle_expect(self.this in that, that=that)

    def not_contained_in(self, that: Iterable[Any]):
        return self._handle_expect(self.this not in that, that=that)

    def has_length(self, length: int):
        return self._handle_expect(len(self.this) == length, that=length)

    def not_has_length(self, length: int):
        return self._handle_expect(len(self.this) != length, that=length)

    def instance_of(self, type: Type):
        return self._handle_expect(isinstance(self.this, type), that=type)

    def not_instance_of(self, type: Type):
        return self._handle_expect(not isinstance(self.this, type), that=type)

    def satisfies(self, predicate: Callable[["expect"], bool]):
        return self._handle_expect(predicate(self.this), that=predicate)

    def not_satisfies(self, predicate: Callable[["expect"], bool]):
        return self._handle_expect(not predicate(self.this), that=predicate)

    def identical_to(self, that: Any):
        return self._handle_expect(self.this is that, that=that)

    def not_identical_to(self, that: Any):
        return self._handle_expect(self.this is not that, that=that)

    def approx(self, that: Any, rel_tol: float = 1e-9, abs_tol: float = 0.0):
        return self._handle_expect(
            math.isclose(self.this, that, abs_tol=abs_tol, rel_tol=rel_tol),
            that=that,
            rel_tol=rel_tol,
            abs_tol=abs_tol,
        )

    def not_approx(self, that: Any, rel_tol: float = 1e-9, abs_tol: float = 0.0):
        return self._handle_expect(
            not math.isclose(self.this, that, abs_tol=abs_tol, rel_tol=rel_tol),
            that=that,
            rel_tol=rel_tol,
            abs_tol=abs_tol,
        )

    def called(self):
        return self._handle_expect(self.this.called)

    def not_called(self):
        return self._handle_expect(not self.this.called)

    def called_once_with(self, *args, **kwargs):
        try:
            self.this.assert_called_once_with(*args, **kwargs)
            passed = True
        except AssertionError:
            passed = False
        return self._handle_expect(passed, *args, **kwargs)

    def called_with(self, *args, **kwargs):
        try:
            self.this.assert_called_with(*args, **kwargs)
            passed = True
        except AssertionError:
            passed = False
        return self._handle_expect(passed, *args, **kwargs)

    def has_calls(self, calls: List[_Call], any_order: bool = False):
        try:
            self.this.assert_has_calls(calls, any_order=any_order)
            passed = True
        except AssertionError:
            passed = False
        return self._handle_expect(passed, calls=calls, any_order=any_order)

    def _store_in_history(
        self,
        result: bool,
        called_with_args: Tuple[Any],
        called_with_kwargs: Dict[str, Any],
        that: Any = None,
    ) -> bool:
        self.history.append(
            Expected(
                this=self.this,
                op=inspect.stack()[2].function,  # :)
                that=that,
                success=result,
                op_args=called_with_args,
                op_kwargs=called_with_kwargs,
            )
        )
        return result

    def _fail_if_false(self, val: bool) -> bool:
        if val:
            return True
        raise ExpectationFailed("expectation failed", self.history)

    def _handle_expect(
        self, result: bool, *args, that: Any = None, **kwargs
    ) -> "expect":
        self._store_in_history(
            result, that=that, called_with_args=args, called_with_kwargs=kwargs
        )
        self._fail_if_false(result)
        return self
