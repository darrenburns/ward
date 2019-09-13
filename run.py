import argparse
from typing import Any, Dict

from blessings import Terminal

from python_tester.collect import get_info_for_modules, get_tests_in_modules, load_modules
from python_tester.fixtures import fixture_registry
from python_tester.suite import Suite
from python_tester.terminal import write_test_results_to_terminal


def setup_cmd_line():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="path of directory containing tests")
    return parser


def run():
    term = Terminal()

    cmd_line = setup_cmd_line()
    args: Dict[str, Any] = vars(cmd_line.parse_args())

    path_to_tests = args.get("path", ".") or "."
    mod_infos = get_info_for_modules(path_to_tests)
    modules = load_modules(mod_infos)
    tests = list(get_tests_in_modules(modules))
    
    suite = Suite(
        tests=tests,
        fixture_registry=fixture_registry,
    )

    test_results = suite.generate_test_runs()
    write_test_results_to_terminal(suite, term, test_results)


if __name__ == "__main__":
    run()
