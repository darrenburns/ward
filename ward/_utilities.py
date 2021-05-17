import collections
import inspect
from pathlib import Path
from typing import Iterable, Any, Callable, Hashable, TypeVar, Dict, List


def truncate(s: str, num_chars: int) -> str:
    suffix = "..." if len(s) > num_chars else ""
    return s[: num_chars - len(suffix)] + suffix


def find_project_root(paths: Iterable[Path]) -> Path:
    if not paths:
        return Path("/").resolve()

    common_base = min(path.resolve() for path in paths)
    if common_base.is_dir():
        common_base /= "child-of-base"

    # Check this common base and all of its parents for files
    # indicating the project root
    for directory in common_base.parents:
        if (directory / "pyproject.toml").is_file():
            return directory
        if (directory / ".git").exists():
            return directory
        if (directory / ".hg").is_dir():
            return directory

    return directory


def get_absolute_path(object: Any) -> Path:
    return Path(inspect.getfile(object)).absolute()


T = TypeVar("T")
H = TypeVar("H", bound=Hashable)


def group_by(items: Iterable[T], key: Callable[[T], H]) -> Dict[H, List[T]]:
    groups = collections.defaultdict(list)
    for item in items:
        groups[key(item)].append(item)
    return dict(groups)
