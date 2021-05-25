import uuid
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from timeit import default_timer
from typing import Any, Callable, Dict, List, Optional, Tuple

# Tests declared with the name _, and with the @test decorator
# have to be stored in here, so that they can later be retrieved.
# They cannot be retrieved directly from the module due to name
# clashes. When we're later looking for tests inside the module,
# we can retrieve any anonymous tests from this dict.
# Map of module absolute Path to list of tests in the module
COLLECTED_TESTS: Dict[Path, List[Callable]] = defaultdict(list)


@dataclass
class Each:
    args: Tuple[Any]

    def __getitem__(self, args):
        return self.args[args]

    def __len__(self):
        return len(self.args)


def _generate_id():
    return uuid.uuid4().hex


class _FormatDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def is_test_module_name(module_name: str) -> bool:
    return module_name.startswith("test_") or module_name.endswith("_test")


class _Timer:
    def __init__(self, duration: Optional[float] = None):
        self._start_time = None
        self.duration = duration

    def __enter__(self):
        self._start_time = default_timer()
        return self

    def __exit__(self, *args):
        self.duration = default_timer() - self._start_time
