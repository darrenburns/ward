import argparse
import pkgutil
from typing import Any, Dict

from python_tester.collect.fixtures import fixture_registry
from python_tester.collect.modules import get_info_for_modules, load_modules
from python_tester.runner.runner import run_tests_in_modules


def setup_cmd_line():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="path of directory containing tests")
    return parser


def is_test_module(module: pkgutil.ModuleInfo) -> bool:
    return module.name.startswith("test_")


def run():
    print("... Running! ...")

    cmd_line = setup_cmd_line()
    args: Dict[str, Any] = vars(cmd_line.parse_args())

    path_to_tests = args.get("path") or "."

    mod_infos = get_info_for_modules(path_to_tests)
    test_mod_infos = (info for info in mod_infos if is_test_module(info))
    modules = load_modules(test_mod_infos)
    test_results = run_tests_in_modules(modules, fixture_registry)

    # Fixtures are now loaded (since the modules have been loaded)
    print("Loaded fixtures", set(fixture_registry.get_all()))

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
