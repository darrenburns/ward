from types import ModuleType

from python_tester.fixtures import FixtureRegistry, fixture, Fixture
from python_tester.suite import Suite
from python_tester.test import Test

NUMBER_OF_TESTS = 5


@fixture
def example_test():
    return Test(
        lambda: 1, (), ModuleType("test_module")
    )


@fixture
def fixtures():
    return {
        "fixture_a": Fixture("fixture_a", lambda: 1),
        "fixture_b": Fixture("fixture_b", lambda: 2),
    }


@fixture
def fixture_registry(fixtures):
    registry = FixtureRegistry()
    registry._fixtures = fixtures
    return registry


@fixture
def suite(example_test, fixture_registry):
    return Suite(
        tests=[example_test] * NUMBER_OF_TESTS,
        fixture_registry=fixture_registry
    )


def test_suite_num_tests(suite):
    assert suite.num_tests == NUMBER_OF_TESTS


def test_suite_num_fixtures(suite, fixtures):
    assert suite.num_fixtures == len(fixtures)
