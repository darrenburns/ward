import argparse
from typing import Any, Dict

from python_tester.collect.find_tests import get_test_module_infos, load_test_modules, run_tests_in_modules

parser = argparse.ArgumentParser()

parser.add_argument('--path', help='path of directory containing tests')


def run():
    print("... Running! ...")
    args: Dict[str, Any] = vars(parser.parse_args())

    path_to_tests = args.get("path") or "."

    mod_info = get_test_module_infos(path_to_tests)
    mods = load_test_modules(mod_info)
    test_results = run_tests_in_modules(mods)

    for result in test_results:
        print(result)


if __name__ == "__main__":
    run()
