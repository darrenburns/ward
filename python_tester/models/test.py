from typing import Callable, Any


class Test:
    def __init__(self, test_function: Callable, module: Any):
        self.test_function = test_function
        self.module = module

    def __call__(self, *args, **kwargs):
        return self.test_function(*args, **kwargs)

    def get_test_name(self):
        return self.test_function.__name__
