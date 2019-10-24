from unittest import mock

from ward import expect, fixture
from ward.fixtures import Fixture, FixtureRegistry
from ward.suite import Suite
from ward.test_result import TestOutcome, TestResult
from ward.testing import SkipMarker, Test, test, xfail

NUMBER_OF_TESTS = 5


@fixture
def module():
    return "test_module"


@fixture
def fixtures():
    return {
        "fixture_a": Fixture(key="fixture_a", fn=lambda fixture_b: fixture_b * 2),
        "fixture_b": Fixture(key="fixture_b", fn=lambda: 2),
    }


@fixture
def example_test(module, fixtures):
    return Test(fn=lambda fixture_a: fixture_a, module_name=module)


@fixture
def skipped_test(module):
    return Test(fn=lambda: expect(1).equals(1), module_name=module, marker=SkipMarker())


@fixture
def fixture_registry(fixtures):
    registry = FixtureRegistry()
    registry._fixtures = fixtures
    return registry


@fixture
def suite(example_test, fixture_registry):
    return Suite(tests=[example_test] * NUMBER_OF_TESTS, fixture_registry=fixture_registry)


@test(f"Suite.num_tests returns {NUMBER_OF_TESTS}, when the suite has {NUMBER_OF_TESTS} tests")
def _(suite):
    expect(suite.num_tests).equals(NUMBER_OF_TESTS)


@test(f"Suite.num_fixtures returns {len(fixtures())}, when the suite has {len(fixtures())} fixtures")
def _(suite, fixtures):
    expect(suite.num_fixtures).equals(len(fixtures))


@test(f"Suite.generate_test_runs generates {NUMBER_OF_TESTS} when suite has {NUMBER_OF_TESTS} tests")
def _(suite):
    runs = suite.generate_test_runs()

    expect(list(runs)).has_length(NUMBER_OF_TESTS)


@test("Suite.generate_test_runs generates yields the expected test results")
def _(suite):
    results = list(suite.generate_test_runs())

    expect(results).equals(
        [TestResult(test=test, outcome=TestOutcome.PASS, error=None, message="") for test in suite.tests]
    )


@test("Suite.generate_test_runs yields a FAIL TestResult on `assert False`")
def _(fixture_registry, module):
    def test_i_fail():
        assert False

    test = Test(fn=test_i_fail, module_name=module)
    failing_suite = Suite(tests=[test], fixture_registry=fixture_registry)

    results = failing_suite.generate_test_runs()
    result = next(results)

    expected_result = TestResult(test=test, outcome=TestOutcome.FAIL, error=mock.ANY, message="")

    expect(result).equals(expected_result)
    expect(result.error).instance_of(AssertionError)


@test("Suite.generate_test_runs yields a SKIP TestResult when test has @skip decorator ")
def _(
    fixture_registry, module, skipped_test, example_test
):
    suite = Suite(tests=[example_test, skipped_test], fixture_registry=fixture_registry)

    test_runs = list(suite.generate_test_runs())
    expected_runs = [
        TestResult(example_test, TestOutcome.PASS, None, ""),
        TestResult(skipped_test, TestOutcome.SKIP, None, ""),
    ]

    expect(test_runs).equals(expected_runs)


@test("Suite.generate_test_runs runs fixture teardown code is ran in the expected order")
def _(module):
    events = []

    def fix_a():
        events.append(1)
        yield "a"
        events.append(3)

    def fix_b():
        events.append(2)
        return "b"

    def my_test(fix_a, fix_b):
        expect(fix_a).equals("a")
        expect(fix_b).equals("b")

    reg = FixtureRegistry()
    reg.cache_fixtures(
        fixtures=[
            Fixture(key="fix_a", fn=fix_a),
            Fixture(key="fix_b", fn=fix_b),
        ]
    )

    suite = Suite(tests=[Test(fn=my_test, module_name=module)], fixture_registry=reg)

    # Exhaust the test runs generator
    list(suite.generate_test_runs())

    expect(events).equals([1, 2, 3])


@xfail("Bug: not all fixtures torn down")
@test("Suite.generate_test_runs tears down deep fixtures")
def _(module):
    events = []

    def fix_a():
        events.append(1)
        yield "a"
        events.append(3)

    def fix_b():
        events.append(2)
        return "b"

    def fix_c(fix_a):
        yield "c"
        events.append(4)

    def my_test(fix_a, fix_b):
        expect(fix_a).equals("a")
        expect(fix_b).equals("b")

    reg = FixtureRegistry()
    reg.cache_fixtures(
        fixtures=[
            Fixture(key="fix_a", fn=fix_a),
            Fixture(key="fix_b", fn=fix_b),
            Fixture(key="fix_c", fn=fix_c),
        ]
    )

    suite = Suite(tests=[Test(fn=my_test, module_name=module)], fixture_registry=reg)

    # Exhaust the test runs generator
    list(suite.generate_test_runs())

    expect(events).equals([1, 2, 3, 4])
