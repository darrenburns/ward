import inspect
from typing import Any, Callable, Tuple


class Test:
    def __init__(self, test_function: Callable, parameters: Tuple, module: Any):
        self.test_function = test_function
        self.name = test_function.__name__
        self.parameters = parameters
        self.module = module

    def __call__(self, *args, **kwargs):
        return self.test_function(*args, **kwargs)

    def fn(self):
        return self.test_function

    def has_deps(self):
        test_has_deps = len(inspect.signature(self.test_function).parameters) > 0
        return test_has_deps
