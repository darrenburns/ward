import importlib
import importlib.util
import os
import pkgutil
from importlib._bootstrap import ModuleSpec
from importlib._bootstrap_external import FileFinder
from typing import Any, Generator, Iterable

from ward.test import Test, WardMarker


def is_test_module(module: pkgutil.ModuleInfo) -> bool:
    return module.name.startswith("test_")


def get_info_for_modules(path: str) -> Generator[pkgutil.ModuleInfo, None, None]:
    # Check for modules at the root of the specified path
    for module in pkgutil.iter_modules([path]):
        yield module

    # Now check for modules in every subdirectory
    for root, dirs, _ in os.walk(path):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            for module in pkgutil.iter_modules([dir_path]):
                if is_test_module(module):
                    yield module


def load_modules(modules: Iterable[pkgutil.ModuleInfo]) -> Generator[Any, None, None]:
    for m in modules:
        file_finder: FileFinder = m.module_finder
        spec: ModuleSpec = file_finder.find_spec(m.name)
        mod = importlib.util.module_from_spec(spec)
        if mod.__name__.startswith("test_"):
            spec.loader.exec_module(mod)
            yield mod


def get_tests_in_modules(modules: Iterable[Any], filter: str = "") -> Generator[Test, None, None]:
    for mod in modules:
        for item in dir(mod):
            if item.startswith("test_"):
                test_name = item
                test_fn = getattr(mod, test_name)
                marker = getattr(test_fn, "ward_marker", WardMarker.NONE)
                if test_fn:
                    test = Test(fn=test_fn, module=mod, marker=marker)

                    # Yield tests if there's no filter, or if the filter matches
                    if not filter:
                        yield test
                    elif filter in test.qualified_name:
                        yield test
