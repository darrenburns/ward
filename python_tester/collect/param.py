import functools
from typing import Callable, Any, Mapping

from parametrized import parametrized

from python_tester.models.test import Test

PARAMETRISED_TESTS: Mapping[str, Callable] = {}


class ParametrisedTest(Test):
    def __init__(self, test_function: Callable, module: Any):
        super().__init__(test_function, module)


def with_params(*args, **kwargs):
    arguments = args

    def decorator_with_params(test_func):
        PARAMETRISED_TESTS[get_identifier_for_test(test_func)] = test_func

        @functools.wraps(test_func)
        def wrapped(*args, **kwargs):
            return parametrized(test_func, *args, **kwargs)

        return wrapped

    return decorator_with_params


def is_parametrised(function: Callable):
    wrapped_fn = getattr(function, '__wrapped__', function)
    identifier = get_identifier_for_test(wrapped_fn)
    return identifier and identifier in PARAMETRISED_TESTS


def get_identifier_for_test(test_func: Callable) -> str:
    return f"{get_func_filename(test_func)}::{test_func.__name__}"


def get_func_filename(func: Callable) -> str:
    return func.__code__.co_filename
