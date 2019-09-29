from types import ModuleType
from unittest import mock

from ward.expect import expect
from ward.fixtures import Fixture, FixtureRegistry, fixture
from ward.suite import Suite
from ward.test import Test, skip, WardMarker
from ward.test_result import TestResult, TestOutcome

NUMBER_OF_TESTS = 5


@fixture
def module():
    return ModuleType("test_module")


@fixture
def fixtures():
    return {
        "fixture_a": Fixture(key="fixture_a", fn=lambda fixture_b: fixture_b * 2),
        "fixture_b": Fixture(key="fixture_b", fn=lambda: 2),
    }


@fixture
def example_test(module, fixtures):
    return Test(fn=lambda fixture_a: fixture_a, module=module)


@fixture
def skipped_test(module):
    return Test(fn=lambda: expect(1).equals(1), module=module, marker=WardMarker.SKIP)


@fixture
def fixture_registry(fixtures):
    registry = FixtureRegistry()
    registry._fixtures = fixtures
    return registry


@fixture
def suite(example_test, fixture_registry):
    return Suite(
        tests=[example_test] * NUMBER_OF_TESTS, fixture_registry=fixture_registry
    )


def test_suite_num_tests(suite):
    expect(suite.num_tests).equals(NUMBER_OF_TESTS)


def test_suite_num_fixtures(suite, fixtures):
    expect(suite.num_fixtures).equals(len(fixtures))


def test_generate_test_runs__correct_number_of_runs_generated(suite):
    runs = suite.generate_test_runs()

    expect(list(runs)).has_length(NUMBER_OF_TESTS)


def test_generate_test_runs__yields_correct_test_results_when_exhausted(suite):
    results = list(suite.generate_test_runs())

    expect(results).equals([
        TestResult(test=test, outcome=TestOutcome.PASS, error=None, message="")
        for test in suite.tests
    ])


def test_generate_test_runs__yields_failing_test_result_on_failed_assertion(
    fixture_registry, module
):
    def test_i_fail():
        assert False

    test = Test(fn=test_i_fail, module=module)
    failing_suite = Suite(tests=[test], fixture_registry=fixture_registry)

    results = failing_suite.generate_test_runs()
    result = next(results)

    expected_result = TestResult(
        test=test, outcome=TestOutcome.FAIL, error=mock.ANY, message=""
    )

    expect(result).equals(expected_result)
    expect(result.error).is_instance_of(AssertionError)


def test_generate_test_runs__yields_skipped_test_result_on_test_with_skip_marker(
    fixture_registry, module, skipped_test, example_test
):
    suite = Suite(tests=[example_test, skipped_test], fixture_registry=fixture_registry)

    test_runs = list(suite.generate_test_runs())
    expected_runs = [
        TestResult(example_test, TestOutcome.PASS, None, ""),
        TestResult(skipped_test, TestOutcome.SKIP, None, "abc"),
    ]

    expect(test_runs).equals(expected_runs)


# region example

def get_capitals_from_server():
    return {"glasgow": "scotland", "tokyo": "japan", "london": "england", "warsaw": "poland",
            "berlin": "germany",
            "madrid": "spain"}


@fixture
def cities():
    return {"edinburgh": "scotland", "tokyo": "japan", "london": "england", "warsaw": "poland", "berlin": "germany",
            "masdid": "spain"}


@skip
def test_capital_cities(cities):
    found_cities = get_capitals_from_server()

    def all_keys_less_than_length_10(cities):
        return all(len(k) < 10 for k in cities)

    (expect(found_cities)
     .satisfies(lambda c: all(len(k) < 10 for k in c))
     .satisfies(all_keys_less_than_length_10)
     .is_instance_of(dict)
     .contains("tokyo")
     .has_length(6)
     .equals(cities))

# endregion example
