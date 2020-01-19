import importlib
import importlib.util
import inspect
import os
import pkgutil
from importlib._bootstrap import ModuleSpec
from importlib._bootstrap_external import FileFinder
from pathlib import Path
from typing import Any, Callable, Generator, Iterable, List, Set

from ward.models import WardMeta
from ward.testing import Test, anonymous_tests


def is_test_module(module: pkgutil.ModuleInfo) -> bool:
    return module.name.startswith("test_")


def get_info_for_modules(
    paths: List[Path],
) -> Generator[pkgutil.ModuleInfo, None, None]:
    # If multiple paths are specified, remove duplicates
    paths = list(set(paths))

    checked_dirs: Set[Path] = set(p for p in paths)

    # Check for modules at the root of the specified path (or paths)
    for module in pkgutil.iter_modules([str(p) for p in paths]):
        if is_test_module(module):
            yield module

    # Now check for modules in every subdirectory
    for p in paths:
        for root, dirs, _ in os.walk(str(p)):
            for dir_name in dirs:
                dir_path = Path(root, dir_name)
                # if we have seen this directory before, skip it
                if dir_path not in checked_dirs:
                    checked_dirs.add(dir_path)
                    for module in pkgutil.iter_modules([str(dir_path)]):
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
