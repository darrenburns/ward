import argparse
import pkgutil
import sys
from itertools import cycle
from time import sleep
from typing import Any, Dict

from blessings import Terminal

from python_tester.collect.fixtures import fixture_registry
from python_tester.collect.modules import get_info_for_modules, load_modules
from python_tester.collect.tests import get_tests_in_modules
from python_tester.output.terminal import write_test_result, write_over_progress_bar, write_over_line
from python_tester.runner.runner import run_tests


def setup_cmd_line():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="path of directory containing tests")
    return parser


def is_test_module(module: pkgutil.ModuleInfo) -> bool:
    return module.name.startswith("test_")


def run():
    term = Terminal()

    cmd_line = setup_cmd_line()
    args: Dict[str, Any] = vars(cmd_line.parse_args())

    path_to_tests = args.get("path") or "."

    mod_infos = get_info_for_modules(path_to_tests)
    test_mod_infos = (info for info in mod_infos if is_test_module(info))
    modules = load_modules(test_mod_infos)
    tests = get_tests_in_modules(modules)
    test_results = run_tests(tests, fixture_registry)

    # Fixtures are now loaded (since the modules have been loaded)
    print(f"Found {len(set(fixture_registry.get_all()))} fixtures. Use --show-fixtures to list them.")
    print()


    passed, failed = 0, 0
    spinner = cycle("⠁⠁⠉⠙⠚⠒⠂⠂⠒⠲⠴⠤⠄⠄⠤⠠⠠⠤⠦⠖⠒⠐⠐⠒⠓⠋⠉⠈⠈")
    for result in test_results:
        sleep(0.1)
        if result.was_success:
            passed += 1
        else:
            failed += 1

        write_test_result(str(result), term)

        pass_pct = passed / (passed + failed)
        fail_pct = 1.0 - pass_pct

        write_over_progress_bar(pass_pct, fail_pct, term)
        write_over_line(f"{next(spinner)} {passed} tests passed, {failed} tests failed", 1, term)

        sleep(0.1)

    print(term.move(term.height - 1, 0))



if __name__ == "__main__":
    run()
