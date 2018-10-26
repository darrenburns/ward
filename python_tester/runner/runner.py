import inspect
from typing import Generator, Sequence

from python_tester.models.test_result import TestResult


def run_tests_in_modules(modules: Sequence) -> Generator[TestResult, None, None]:
    for mod in modules:
        for item in dir(mod):
            if item.startswith("test_"):
                test_name = item
                test_fn = getattr(mod, test_name)
                try:
                    if inspect.isfunction(test_fn):
                        test_fn()
                        yield TestResult(test_name, True, None)
                except Exception as e:
                    yield TestResult(test_name, False, e)
