from types import ModuleType

from python_tester.fixtures import Fixture, FixtureRegistry, fixture
from python_tester.suite import Suite
from python_tester.test import Test

NUMBER_OF_TESTS = 5


@fixture
def example_test(fixtures):
    return Test(
        lambda fixture_a: fixture_a, ModuleType("test_module")
    )


@fixture
def fixtures():
    return {
        "fixture_a": Fixture(
            name="fixture_a",
            fn=lambda fixture_b: fixture_b * 2,
        ),
        "fixture_b": Fixture(
            name="fixture_b",
            fn=lambda: 2,
        ),
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


def test_generate_test_runs__correct_number_of_runs_generated(suite):
    runs = suite.generate_test_runs()
    assert len(list(runs)) == NUMBER_OF_TESTS
