import argparse
import pkgutil
from typing import Any, Dict, Sequence

from python_tester.collect.module_loader import get_info_for_modules, load_modules
from python_tester.runner.runner import run_tests_in_modules

parser = argparse.ArgumentParser()

parser.add_argument('--path', help='path of directory containing tests')


class Fixture:
    pass


def is_test_module(module: pkgutil.ModuleInfo) -> bool:
    return module.name.startswith("test_")


def run():
    print("... Running! ...")
    args: Dict[str, Any] = vars(parser.parse_args())

    path_to_tests = args.get("path") or "."

    # fixtures: Sequence[Fixture] = collect_fixtures()

    mod_infos = get_info_for_modules(path_to_tests)
    test_mod_infos = (info for info in mod_infos if is_test_module(info))
    mods = load_modules(test_mod_infos)
    test_results = run_tests_in_modules(mods)

    passed, failed = 0, 0
    for result in test_results:
        if result.was_success:
            passed += 1
        else:
            failed += 1
        print(result)

    print(f"{passed} tests passed, {failed} tests failed")


if __name__ == "__main__":
    run()
