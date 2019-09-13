import importlib
import importlib.util
import os
import pkgutil
from importlib._bootstrap import ModuleSpec
from importlib._bootstrap_external import FileFinder
from typing import Any, Generator, Iterable, List


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


def load_modules(modules: Iterable[pkgutil.ModuleInfo]) -> List[Any]:
    loaded = []
    for m in modules:
        file_finder: FileFinder = m.module_finder
        spec: ModuleSpec = file_finder.find_spec(m.name)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        loaded.append(mod)
    return loaded
