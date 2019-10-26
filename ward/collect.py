import importlib
import importlib.util
import inspect
import os
import pkgutil
from importlib._bootstrap import ModuleSpec
from importlib._bootstrap_external import FileFinder
from typing import Any, Callable, Generator, Iterable, List

from ward.testing import Test, anonymous_tests
from ward.models import Marker, WardMeta


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


def get_tests_in_modules(modules: Iterable) -> Generator[Test, None, None]:
    for mod in modules:
        mod_name = mod.__name__
        # Collect anonymous tests from the module
        anon_tests: List[Callable] = anonymous_tests[mod_name]
        if anon_tests:
            for test_fn in anon_tests:
                meta: WardMeta = getattr(test_fn, "ward_meta")
                yield Test(
                    fn=test_fn,
                    module_name=mod_name,
                    marker=meta.marker,
                    description=meta.description or "",
                )

        # Collect named tests from the module
        for item in dir(mod):
            if item.startswith("test_") and not item == "_":
                test_name = item
                test_fn = getattr(mod, test_name)
                marker: Marker = getattr(test_fn, "ward_meta", WardMeta()).marker
                if test_fn:
                    yield Test(fn=test_fn, module_name=mod_name, marker=marker)


def search_generally(
    tests: Iterable[Test], query: str = ""
) -> Generator[Test, None, None]:
    if not query:
        yield from tests

    for test in tests:
        description = test.description or ""
        if (
            query in description
            or query in f"{test.module_name}."
            or query in inspect.getsource(test.fn)
            or query in test.qualified_name
        ):
            yield test
