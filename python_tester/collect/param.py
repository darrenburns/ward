import functools
from typing import Mapping

from python_tester.models.test import Test

PARAMETERISED_TESTS: Mapping[str, Test] = {}


def with_params(*args, **kwargs):
    arguments = args

    def decorator_with_params(test_func):
        @functools.wraps(test_func)
        def wrapped(*args, **kwargs):
            return test_func(*args, **kwargs)

        test = Test(test_func, arguments, None)
        PARAMETERISED_TESTS[test_func] = test

        return wrapped

    return decorator_with_params
