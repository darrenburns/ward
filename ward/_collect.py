import importlib
import importlib.util
import inspect
import os
import pkgutil
import sys
from dataclasses import dataclass
from distutils.sysconfig import get_python_lib
from importlib._bootstrap import ModuleSpec  # type: ignore[import]
from importlib._bootstrap_external import FileFinder  # type: ignore[import]
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


def is_test_module(module: pkgutil.ModuleInfo) -> bool:
    return is_test_module_name(module.name)


def _get_module_path(module: pkgutil.ModuleInfo) -> Path:
    return Path(module.module_finder.find_module(module.name).path)


def _is_excluded_module(module: pkgutil.ModuleInfo, exclusions: Iterable[str]) -> bool:
    return _excluded(_get_module_path(module), exclusions)


def _excluded(path: Path, exclusions: Iterable[str]) -> bool:
    """Return True if path matches any of the `exclude` paths passed by the user. False otherwise."""
    for exclude in exclusions:
        exclusion_path = Path(exclude)
        if exclusion_path == path:
            return True

        try:
            path.resolve().relative_to(exclusion_path.resolve())
        except ValueError:
            # We need to look at the rest of the exclusions
            # to see if they match, so move on to the next one.
            continue
        else:
            return True

    return False


def _remove_excluded_paths(
    paths: Iterable[Path], exclusions: Iterable[str]
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


def configure_path(project_root: Optional[Path]) -> None:
    sys.path.append(".")
    if project_root:
        sys.path.append(str(project_root.resolve()))


# flake8: noqa: C901 - FIXME
def get_info_for_modules(
    paths: List[Path],
    exclude: Tuple[str],
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


@dataclass
class PackageData:
    pkg_name: str
    pkg_root: Path


def load_modules(modules: Iterable[pkgutil.ModuleInfo]) -> List[ModuleType]:
    loaded_modules = []

    for m in modules:
        if hasattr(m, "module_finder"):
            file_finder: FileFinder = m.module_finder
            spec: ModuleSpec = file_finder.find_spec(m.name)
            m = importlib.util.module_from_spec(spec)

        module_name = m.__name__
        if is_test_module_name(module_name):
            pkg_data = _build_package_data(m)
            if pkg_data.pkg_root not in sys.path:
                sys.path.append(str(pkg_data.pkg_root))
            m.__package__ = pkg_data.pkg_name
            m.__loader__.exec_module(m)
            loaded_modules.append(m)

    return loaded_modules


def _build_package_data(module: ModuleType) -> PackageData:
    path = Path(module.__file__).resolve().parent
    package_parts = []
    while path.is_dir() and (path / "__init__.py").exists():
        package_parts.append(path.stem)
        path = path.parent
    package_name = ".".join(reversed(package_parts))
    return PackageData(
        pkg_name="" if package_name == "." else package_name,
        pkg_root=path.resolve(),
    )


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
