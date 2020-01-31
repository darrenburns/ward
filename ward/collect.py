import importlib
import importlib.util
import inspect
import pkgutil
from collections import defaultdict
from importlib._bootstrap import ModuleSpec
from importlib._bootstrap_external import FileFinder
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterable, List

from ward.models import WardMeta
from ward.testing import Test, anonymous_tests, is_test_module_name
from ward.util import get_absolute_path


def is_test_module(module: pkgutil.ModuleInfo) -> bool:
    return is_test_module_name(module.name)


def get_info_for_modules(
    paths: List[Path],
) -> Generator[pkgutil.ModuleInfo, None, None]:
    # iter_modules does not work on normal files, so if passed a file, we iterate over its parent
    # directory and match against its name

    # If multiple paths are specified, remove duplicates
    paths = list(set(paths))

    # Split files from directories. Files are stored with their parent directory, so we don't
    # iterate over them multiple times.
    files: Dict[Path, List[str]] = defaultdict(list)
    dirs = []
    for p in paths:
        if p.is_file():
            files[p.parent].append(p.stem)
        elif p.is_dir():
            dirs.append(p)

    # Handle normal files
    for parent, files_ in files.items():
        for module in pkgutil.iter_modules([str(parent)]):
            if module.name in files_ and is_test_module(module):
                yield module

    # Handle directories
    for module in pkgutil.walk_packages(path=[str(d) for d in dirs]):
        if is_test_module(module):
            print(module)
            yield module


def load_modules(modules: Iterable[pkgutil.ModuleInfo]) -> Generator[Any, None, None]:
    for m in modules:
        file_finder: FileFinder = m.module_finder
        spec: ModuleSpec = file_finder.find_spec(m.name)
        mod = importlib.util.module_from_spec(spec)
        if mod.__name__.startswith("test_"):
            spec.loader.exec_module(mod)
            yield mod


def get_tests_in_modules(
    modules: Iterable, capture_output: bool = True
) -> Generator[Test, None, None]:
    for mod in modules:
        mod_name = mod.__name__
        mod_path = get_absolute_path(mod)
        anon_tests: List[Callable] = anonymous_tests[mod_path]
        if anon_tests:
            for test_fn in anon_tests:
                meta: WardMeta = getattr(test_fn, "ward_meta")
                yield Test(
                    fn=test_fn,
                    module_name=mod_name,
                    marker=meta.marker,
                    description=meta.description or "",
                    capture_output=capture_output,
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
