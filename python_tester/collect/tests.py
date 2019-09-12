from typing import Any, Generator, Iterable

from python_tester.models.test import Test


def get_tests_in_modules(
    modules: Iterable[Any]
) -> Generator[Test, None, None]:
    for mod in modules:
        for item in dir(mod):
            if item.startswith("test_"):
                test_name = item
                test_fn = getattr(mod, test_name)
                yield Test(test_fn, [], mod)
