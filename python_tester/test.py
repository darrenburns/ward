import inspect
from types import MappingProxyType
from typing import Any, Callable, Tuple


class Test:
    def __init__(self, test_function: Callable, parameters: Tuple, module: Any):
        self.test_function = test_function
        self.parameters = parameters
        self.module = module

        self.name = test_function.__name__

    def __call__(self, *args, **kwargs):
        breakpoint()
        return self.test_function(*args, **kwargs)

    def fn(self) -> Callable:
        return self.test_function

    def deps(self) -> MappingProxyType:
        return inspect.signature(self.fn()).parameters

    def has_deps(self) -> bool:
        return len(self.deps()) > 0
