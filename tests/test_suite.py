from types import ModuleType
from unittest.mock import create_autospec

from python_tester.fixtures import FixtureRegistry, fixture
from python_tester.suite import Suite
from python_tester.test import Test

NUMBER_OF_TESTS = 5


@fixture
def example_test():
    return Test(
        lambda: 1, (), ModuleType("test_module")
    )


@fixture
def fixture_registry():
    return create_autospec(FixtureRegistry)


@fixture
def suite(example_test, fixture_registry):
    return Suite(
        tests=[example_test] * NUMBER_OF_TESTS,
        fixture_registry=fixture_registry
    )


def test_suite_num_tests(suite):
    assert suite.num_tests == NUMBER_OF_TESTS
