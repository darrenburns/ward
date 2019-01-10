from typing import Iterable, Any, Generator, Callable

from python_tester.models.test import Test


def get_tests_in_modules(
    modules: Iterable[Any]
) -> Generator[Callable, None, None]:
    for mod in modules:
        for item in dir(mod):
            if item.startswith("test_"):
                test_name = item
                test_fn = getattr(mod, test_name)
                yield Test(test_fn, mod)