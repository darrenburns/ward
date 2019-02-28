from typing import Callable, Any, Tuple


class Test:
    def __init__(self, test_function: Callable, parameters: Tuple, module: Any):
        self.test_function = test_function
        self.parameters = parameters
        self.module = module

    def __call__(self, *args, **kwargs):
        return self.test_function(*args, **kwargs)

    @property
    def is_parameterised(self):
        return len(self.parameters) > 0

    def get_test_name(self):
        return self.test_function.__name__
