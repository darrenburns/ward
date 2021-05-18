import uuid
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Any, Dict, Callable, List

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


