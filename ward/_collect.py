import importlib
import importlib.util
import inspect
import os
import pkgutil
import sys
from distutils.sysconfig import get_python_lib
from importlib._bootstrap import ModuleSpec
from importlib._bootstrap_external import FileFinder
from pathlib import Path
from types import ModuleType
from typing import Callable, Iterable, List, Optional, Set, Tuple

from cucumber_tag_expressions.model import Expression

from ward._errors import CollectionError
from ward._testing import COLLECTED_TESTS, is_test_module_name
from ward._utilities import get_absolute_path
from ward.fixtures import Fixture
from ward.models import CollectionMetadata
from ward.testing import Test

Glob = str


def is_test_module(module: pkgutil.ModuleInfo) -> bool:
    return is_test_module_name(module.name)


def _get_module_path(module: pkgutil.ModuleInfo) -> Path:
    return Path(module.module_finder.find_module(module.name).path)


def _is_excluded_module(module: pkgutil.ModuleInfo, exclusions: Iterable[Glob]) -> bool:
    return _excluded(_get_module_path(module), exclusions)


def _excluded(path: Path, exclusions: Iterable[Glob]) -> bool:
    """Return True if path matches any of the glob patterns in exclusions. False otherwise."""
    return any(path.match(pattern) for pattern in exclusions)


def _remove_excluded_paths(
    paths: Iterable[Path], exclusions: Iterable[Glob]
) -> List[Path]:
    return [p for p in paths if not _excluded(p, exclusions)]


def _handled_within(module_path: Path, search_paths: Iterable[Path]) -> bool:
    """
    Return True if the module path starts with any of the search paths,
    that is, if any module is contained within any of the search paths
    """
    for search_path in search_paths:
        if search_path.is_dir():
            if search_path in module_path.parents:
                return True
    return False


# flake8: noqa: C901 - FIXME
def get_info_for_modules(
    paths: List[Path],
    exclude: Tuple[Glob],
) -> List[pkgutil.ModuleInfo]:
    paths = _remove_excluded_paths(set(paths), exclude)

    module_infos = []

    # Handle case where path points directly to modules
    for path in paths:
        if path.is_file() and not _handled_within(path, paths):
            spec = importlib.util.spec_from_file_location(path.stem, path)
            try:
                mod = importlib.util.module_from_spec(spec)
            except AttributeError as e:
                msg = f"Path {str(path)} is not a valid Python module."
                raise CollectionError(msg) from e
            module_infos.append(mod)

    # Check for modules at the root of the specified path (or paths)
    for mod in pkgutil.iter_modules([str(p) for p in paths if p.is_dir()]):
        if is_test_module(mod) and not _is_excluded_module(mod, exclude):
            module_infos.append(mod)

    # Now check for modules in every subdirectory
    checked_dirs: Set[Path] = set(p for p in paths)
    for p in paths:
        for root, dirs, _ in os.walk(str(p)):
            if _excluded(Path(root), exclude):
                continue
            for dir_name in dirs:
                dir_path = Path(root, dir_name)

                # ignore site-packages directories
                abs_path = dir_path.absolute()
                if str(abs_path).startswith(get_python_lib()):
                    continue

                # if we have seen this path before, skip it
                if dir_path not in checked_dirs and not _excluded(dir_path, exclude):
                    checked_dirs.add(dir_path)
                    for mod in pkgutil.iter_modules([str(dir_path)]):
                        if is_test_module(mod) and not _is_excluded_module(
                            mod, exclude
                        ):
                            module_infos.append(mod)

    return module_infos


def load_modules(modules: Iterable[ModuleSpec]) -> List[ModuleType]:
    loaded_modules = []

    for m in modules:
        if hasattr(m, "module_finder"):
            file_finder: FileFinder = m.module_finder
            spec: ModuleSpec = file_finder.find_spec(m.name)
            m = importlib.util.module_from_spec(spec)

        module_name = m.__name__
        if is_test_module_name(module_name):
            if module_name not in sys.modules:
                sys.modules[module_name] = m
            m.__package__ = _build_package_name(m)
            m.__loader__.exec_module(m)
            loaded_modules.append(m)

    return loaded_modules


def _build_package_name(module: ModuleType) -> str:
    path_without_ext: str = module.__file__.rpartition(".")[0]
    path_with_dots: str = path_without_ext.replace(os.path.sep, ".")
    package_name: str = path_with_dots.rpartition(".")[0]
    return "" if package_name == "." else package_name


def get_tests_in_modules(modules: Iterable, capture_output: bool = True) -> List[Test]:
    tests = []
    for mod in modules:
        mod_name = mod.__name__
        mod_path = get_absolute_path(mod)
        anon_tests: List[Callable] = COLLECTED_TESTS[mod_path]
        if anon_tests:
            for test_fn in anon_tests:
                meta: CollectionMetadata = getattr(test_fn, "ward_meta")
                tests.append(
                    Test(
                        fn=test_fn,
                        module_name=mod_name,
                        marker=meta.marker,
                        description=meta.description or "",
                        capture_output=capture_output,
                        tags=meta.tags or [],
                    )
                )
    return tests


def filter_tests(
    tests: List[Test],
    query: str = "",
    tag_expr: Optional[Expression] = None,
) -> List[Test]:
    if not query and not tag_expr:
        return tests

    filtered_tests = []
    for test in tests:
        description = test.description or ""

        matches_query = (
            not query
            or query in description
            or query in f"{test.module_name}."
            or query in inspect.getsource(test.fn)
            or query in test.qualified_name
        )

        matches_tags = not tag_expr or tag_expr.evaluate(test.tags)

        if matches_query and matches_tags:
            filtered_tests.append(test)

    return filtered_tests


def filter_fixtures(
    fixtures: List[Fixture],
    query: str = "",
    paths: Optional[Iterable[Path]] = None,
) -> List[Fixture]:
    if paths is None:
        paths = []
    paths = {path.absolute() for path in paths}

    filtered_fixtures = []
    for fixture in fixtures:
        matches_query = (
            not query
            or query in f"{fixture.module_name}."
            or query in inspect.getsource(fixture.fn)
            or query in fixture.qualified_name
        )

        matches_paths = (
            not paths
            or fixture.path in paths
            or any(parent in paths for parent in fixture.path.parents)
        )

        if matches_query and matches_paths:
            filtered_fixtures.append(fixture)

    return filtered_fixtures
