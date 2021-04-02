import importlib
import importlib.util
import inspect
import os
import pkgutil
from distutils.sysconfig import get_python_lib
from pathlib import Path
from types import ModuleType
from typing import (
    Any,
    Callable,
    Generator,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Iterator,
    Collection,
)

import sys
from cucumber_tag_expressions.model import Expression
from importlib._bootstrap import ModuleSpec
from importlib._bootstrap_external import FileFinder

from ward.errors import CollectionError
from ward.fixtures import Fixture
from ward.models import WardMeta
from ward.testing import Test, anonymous_tests, is_test_module_name
from ward.util import get_absolute_path

Glob = str


def is_test_module(module: ModuleType) -> bool:
    return is_test_module_name(module.name)


def _get_module_path(module: ModuleType) -> Path:
    return Path(module.module_finder.find_module(module.name).path)


def _is_excluded_module(module: ModuleType, exclusions: Iterable[Glob]) -> bool:
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


def get_info_for_modules(
    paths: List[Path], exclude: Tuple[Glob],
) -> Generator[pkgutil.ModuleInfo, None, None]:
    paths = _remove_excluded_paths(set(paths), exclude)

    # Handle case where path points directly to modules
    for path in paths:
        if path.is_file() and not _handled_within(path, paths):
            spec = importlib.util.spec_from_file_location(path.stem, path)
            try:
                mod = importlib.util.module_from_spec(spec)
            except AttributeError as e:
                msg = f"Path {str(path)} is not a valid Python module."
                raise CollectionError(msg) from e
            yield mod

    # Check for modules at the root of the specified path (or paths)
    for mod in pkgutil.iter_modules([str(p) for p in paths if p.is_dir()]):
        if is_test_module(mod) and not _is_excluded_module(mod, exclude):
            yield mod

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
                            yield mod


def load_modules(modules: Iterable[ModuleType]) -> Generator[Any, None, None]:
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
            yield m


def _build_package_name(module: ModuleType) -> str:
    path_without_ext: str = module.__file__.rpartition(".")[0]
    path_with_dots: str = path_without_ext.replace(os.path.sep, ".")
    package_name: str = path_with_dots.rpartition(".")[0]
    return "" if package_name == "." else package_name


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
                    tags=meta.tags or [],
                )


def filter_tests(
    tests: Iterable[Test], query: str = "", tag_expr: Optional[Expression] = None,
) -> Iterator[Test]:
    if not query and not tag_expr:
        yield from tests

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
            yield test


def filter_fixtures(
    fixtures: Iterable[Fixture],
    query: str = "",
    paths: Optional[Collection[Path]] = None,
) -> Iterator[Fixture]:
    if paths is None:
        paths = []
    paths = {path.absolute() for path in paths}

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
            yield fixture
