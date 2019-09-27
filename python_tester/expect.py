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


class ExpectationError(Exception):
    def __init__(self, message: str, this: Any, that: Any, method: str):
        self.message = message
        self.this = this
        self.that = that
        self.method = method


class expect:
    def __init__(self, this: Any):
        self.this = this

    def equals(self, that: Any) -> "expect":
        if self.this == that:
            return self
        raise ExpectationError(
            "Equality test failed",
            self.this,
            that,
            self.equals.__name__,
        )

    def less_than(self, that: Any) -> "expect":
        if self.this < that:
            return self
        raise ExpectationError(
            "Less than check failed",
            self.this,
            that,
            self.less_than.__name__,
        )
