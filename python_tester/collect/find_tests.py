import importlib
import importlib.util
import os
import pkgutil
from importlib._bootstrap import ModuleSpec
from importlib._bootstrap_external import FileFinder
from typing import Any, Generator, Optional


class TestResult:
    def __init__(self, test_name: str, was_success: bool, error: Optional[Exception]):
        self.test_name = test_name
        self.was_success = was_success
        self.error = error

    def __str__(self):
        status = "PASS" if self.was_success else "FAIL"
        return f"[{status}] {self.test_name}"


def get_test_module_infos(path: str) -> Generator[pkgutil.ModuleInfo, None, None]:

    def is_test_module(module: pkgutil.ModuleInfo) -> bool:
        return module.name.startswith("test_")

    # Check for modules at the root of the specified path
    for module in pkgutil.iter_modules([path]):
        if is_test_module(module):
            yield module

    # Now check for modules in every subdirectory
    for root, dirs, _ in os.walk(path):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            for module in pkgutil.iter_modules([dir_path]):
                if is_test_module(module):
                    yield module


def load_test_modules(modules: Generator[pkgutil.ModuleInfo, None, None]) -> Generator[Any, None, None]:
    for m in modules:
        file_finder: FileFinder = m.module_finder
        spec: ModuleSpec = file_finder.find_spec(m.name)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        yield mod


def run_tests_in_modules(modules: Generator[Any, None, None]) -> Generator[TestResult, None, None]:
    for mod in modules:
        for item in dir(mod):
            if item.startswith("test_"):
                test_name = item
                test_fn = getattr(mod, test_name)
                try:
                    test_fn()
                    yield TestResult(test_name, True, None)
                except Exception as e:
                    yield TestResult(test_name, False, e)
