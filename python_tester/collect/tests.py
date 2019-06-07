from typing import Iterable, Any, Generator

from python_tester.collect.param import PARAMETERISED_TESTS
from python_tester.models.test import Test


def get_tests_in_modules(
        modules: Iterable[Any]
) -> Generator[Test, None, None]:
    for mod in modules:
        for item in dir(mod):
            if item.startswith("test_"):
                test_name = item
                test_fn = getattr(mod, test_name)
                has_params = getattr(test_fn, "__wrapped__", None) in PARAMETERISED_TESTS.keys()
                if has_params:
                    paramed_test = PARAMETERISED_TESTS[test_fn.__wrapped__]
                    yield Test(paramed_test.test_function, paramed_test.parameters, mod)
                else:
                    yield Test(test_fn, [], mod)
