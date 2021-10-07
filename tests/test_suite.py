from unittest import mock

from tests.utilities import NUMBER_OF_TESTS, example_test, module, testable_test
from ward import fixture
from ward._errors import ParameterisationError
from ward._suite import Suite
from ward.models import Scope, SkipMarker
from ward.testing import Test, TestOutcome, TestResult, each, skip, test


@fixture
def skipped_test(module=module):
    @testable_test
    def t():
        assert 1 == 1

    return Test(fn=t, module_name=module, marker=SkipMarker())


@fixture
def suite(example_test=example_test):
    return Suite(tests=[example_test] * NUMBER_OF_TESTS)


@test(
    f"Suite.num_tests returns {NUMBER_OF_TESTS}, when the suite has {NUMBER_OF_TESTS} tests"
)
def _(suite=suite):
    assert suite.num_tests == NUMBER_OF_TESTS


@test(
    f"Suite.generate_test_runs generates {NUMBER_OF_TESTS} tests when suite has {NUMBER_OF_TESTS} tests"
)
def _(suite=suite):
    runs = suite.generate_test_runs()

    assert len(list(runs)) == NUMBER_OF_TESTS


@test("Suite.generate_test_runs yields the expected test results")
def _(suite=suite):
    results = list(suite.generate_test_runs())
    expected = [
        TestResult(test=test, outcome=TestOutcome.PASS, error=None, message="")
        for test in suite.tests
    ]
    assert results == expected


@test("Suite.generate_test_runs yields a FAIL TestResult on `assert False`")
def _(module=module):
    @testable_test
    def _():
        assert False

    t = Test(fn=_, module_name=module)
    failing_suite = Suite(tests=[t])

    results = failing_suite.generate_test_runs()
    result = next(results)

    expected_result = TestResult(
        test=t, outcome=TestOutcome.FAIL, error=mock.ANY, message=""
    )
    assert result == expected_result
    assert isinstance(result.error, AssertionError)


@test(
    "Suite.generate_test_runs yields a SKIP TestResult when test has @skip decorator "
)
def _(skipped=skipped_test, example=example_test):
    suite = Suite(tests=[example, skipped])

    test_runs = list(suite.generate_test_runs())
    expected_runs = [
        TestResult(example, TestOutcome.PASS, None, ""),
        TestResult(skipped, TestOutcome.SKIP, None, ""),
    ]

    assert test_runs == expected_runs


@test("Suite.generate_test_runs yields a DRYRUN TestResult when dry_run is True")
def _(skipped=skipped_test, example=example_test):
    suite = Suite(tests=[example, skipped])

    test_runs = list(suite.generate_test_runs(dry_run=True))

    expected_runs = [
        TestResult(example, TestOutcome.DRYRUN, None, ""),
        TestResult(skipped, TestOutcome.DRYRUN, None, ""),
    ]

    assert test_runs == expected_runs


@test("Suite.generate_test_runs fixture teardown code runs in the expected order")
def _(module=module):
    events = []

    @fixture
    def fix_a():
        events.append(1)
        yield "a"
        events.append(3)

    @fixture
    def fix_b():
        events.append(2)
        return "b"

    @testable_test
    def my_test(fix_a=fix_a, fix_b=fix_b):
        assert fix_a == "a"
        assert fix_b == "b"

    suite = Suite(tests=[Test(fn=my_test, module_name=module)])

    # Exhaust the test runs generator
    list(suite.generate_test_runs())

    assert events == [1, 2, 3]


@test(
    "Suite.generate_test_runs exception in teardown of test-scoped fixture fails dependent tests"
)
def _(module=module):
    events = []
    error_message = "example"
    teardown_err = ZeroDivisionError(error_message)

    @fixture
    def fix_a():
        events.append(1)
        yield "a"
        raise teardown_err

    @testable_test
    def my_test(fix_a=fix_a):
        assert fix_a == "a"

    test_obj = Test(fn=my_test, module_name=module)
    suite = Suite(tests=[test_obj])

    results = list(suite.generate_test_runs())

    assert results == [
        TestResult(
            test=test_obj,
            outcome=TestOutcome.FAIL,
            error=teardown_err,
            message=error_message,
        )
    ]


@test("Suite.generate_test_runs tears down deep fixtures")
def _(module=module):
    events = []

    @fixture
    def fix_a():
        events.append(1)
        yield "a"
        events.append(4)

    @fixture
    def fix_b():
        events.append(2)
        return "b"

    @fixture
    def fix_c(fix_b=fix_b):
        events.append(3)
        yield "c"
        events.append(5)

    @testable_test
    def my_test(fix_a=fix_a, fix_c=fix_c):
        assert fix_a == "a"
        assert fix_c == "c"

    suite = Suite(tests=[Test(fn=my_test, module_name=module)])

    # Exhaust the test runs generator
    list(suite.generate_test_runs())

    assert events == [1, 2, 3, 4, 5]


@test("Suite.generate_test_runs cached fixture isn't executed again")
def _(module=module):
    events = []

    @fixture
    def a():
        events.append(1)

    # Both of the fixtures below depend on 'a', but 'a' should only be executed once.
    @fixture
    def b(a=a):
        events.append(2)

    @fixture
    def c(a=a):
        events.append(3)

    @testable_test
    def test(b=b, c=c):
        pass

    suite = Suite(tests=[Test(fn=test, module_name=module)])

    list(suite.generate_test_runs())

    assert events == [1, 2, 3]


@test("Suite.generate_test_runs correctly tears down module scoped fixtures")
def _():
    events = []

    @fixture(scope=Scope.Module)
    def a():
        events.append("resolve")
        yield "a"
        events.append("teardown")

    @testable_test
    def test1(a=a):
        events.append("test1")

    @testable_test
    def test2(a=a):
        events.append("test2")

    @testable_test
    def test3(a=a):
        events.append("test3")

    # For testing purposes we need to assign paths ourselves,
    # since our test functions are all defined at the same path
    test1.ward_meta.path = "module1"
    test2.ward_meta.path = "module2"
    test3.ward_meta.path = "module2"

    suite = Suite(
        tests=[
            Test(fn=test1, module_name="module1"),
            Test(fn=test2, module_name="module2"),
            Test(fn=test3, module_name="module2"),
        ]
    )

    list(suite.generate_test_runs())

    assert events == [
        "resolve",  # Resolve at start of module1
        "test1",
        "teardown",  # Teardown at end of module1
        "resolve",  # Resolve at start of module2
        "test2",
        "test3",
        "teardown",  # Teardown at end of module2
    ]


@test("Suite.generate_test_runs resolves and tears down global fixtures once only")
def _():
    events = []

    @fixture(scope=Scope.Global)
    def a():
        events.append("resolve")
        yield "a"
        events.append("teardown")

    @testable_test
    def test1(a=a):
        events.append("test1")

    @testable_test
    def test2(a=a):
        events.append("test2")

    @testable_test
    def test3(a=a):
        events.append("test3")

    suite = Suite(
        tests=[
            Test(fn=test1, module_name="module1"),
            Test(fn=test2, module_name="module2"),
            Test(fn=test3, module_name="module2"),
        ]
    )

    list(suite.generate_test_runs())

    assert events == [
        "resolve",  # Resolve at start of run only
        "test1",
        "test2",
        "test3",
        "teardown",  # Teardown only at end of run
    ]


@test("Suite.generate_test_runs resolves mixed scope fixtures correctly")
def _():
    events = []

    @fixture(scope=Scope.Global)
    def a():
        events.append("resolve a")
        yield "a"
        events.append("teardown a")

    @fixture(scope=Scope.Module)
    def b():
        events.append("resolve b")
        yield "b"
        events.append("teardown b")

    @fixture(scope=Scope.Test)
    def c():
        events.append("resolve c")
        yield "c"
        events.append("teardown c")

    @testable_test
    def test_1(a=a, b=b, c=c):
        events.append("test1")

    @testable_test
    def test_2(a=a, b=b, c=c):
        events.append("test2")

    @testable_test
    def test_3(a=a, b=b, c=c):
        events.append("test3")

    test_1.ward_meta.path = "module1"
    test_2.ward_meta.path = "module2"
    test_3.ward_meta.path = "module1"

    suite = Suite(
        tests=[
            # Module ordering is intentionally off here, to ensure correct
            # interaction between module-scope fixtures and random ordering
            Test(fn=test_1, module_name="module1"),
            Test(fn=test_2, module_name="module2"),
            Test(fn=test_3, module_name="module1"),
        ]
    )

    list(suite.generate_test_runs())

    assert events == [
        "resolve a",  # global fixture so resolved at start
        "resolve b",  # module fixture resolved at start of module1
        "resolve c",  # test fixture resolved at start of test1
        "test1",
        "teardown c",  # test fixture teardown at start of test1
        "resolve b",  # module fixture resolved at start of module2
        "resolve c",  # test fixture resolved at start of test2
        "test2",
        "teardown c",  # test fixture teardown at start of test2
        "teardown b",  # module fixture teardown at end of module2
        "resolve c",  # test fixture resolved at start of test3
        "test3",
        "teardown c",  # test fixture teardown at end of test3
        "teardown b",  # module fixture teardown at end of module1
        "teardown a",  # global fixtures are torn down at the very end
    ]


@test("Suite.generate_test_runs resolves mixed scope async fixtures correctly")
def _():
    events = []

    @fixture(scope=Scope.Global)
    async def a():
        events.append("resolve a")
        yield "a"
        events.append("teardown a")

    @fixture(scope=Scope.Module)
    async def b():
        events.append("resolve b")
        yield "b"
        events.append("teardown b")

    @fixture(scope=Scope.Test)
    async def c():
        events.append("resolve c")
        yield "c"
        events.append("teardown c")

    @testable_test
    async def test_1(a=a, b=b, c=c):
        events.append("test1")

    @testable_test
    async def test_2(a=a, b=b, c=c):
        events.append("test2")

    @testable_test
    async def test_3(a=a, b=b, c=c):
        events.append("test3")

    test_1.ward_meta.path = "module1"
    test_2.ward_meta.path = "module2"
    test_3.ward_meta.path = "module1"

    suite = Suite(
        tests=[
            # Module ordering is intentionally off here, to ensure correct
            # interaction between module-scope fixtures and random ordering
            Test(fn=test_1, module_name="module1"),
            Test(fn=test_2, module_name="module2"),
            Test(fn=test_3, module_name="module1"),
        ]
    )

    list(suite.generate_test_runs())

    assert events == [
        "resolve a",  # global fixture so resolved at start
        "resolve b",  # module fixture resolved at start of module1
        "resolve c",  # test fixture resolved at start of test1
        "test1",
        "teardown c",  # test fixture teardown at start of test1
        "resolve b",  # module fixture resolved at start of module2
        "resolve c",  # test fixture resolved at start of test2
        "test2",
        "teardown c",  # test fixture teardown at start of test2
        "teardown b",  # module fixture teardown at end of module2
        "resolve c",  # test fixture resolved at start of test3
        "test3",
        "teardown c",  # test fixture teardown at end of test3
        "teardown b",  # module fixture teardown at end of module1
        "teardown a",  # global fixtures are torn down at the very end
    ]


@skip("TODO: Determine how this should behave")
@test(
    "Suite.generate_test_runs dependent fixtures of differing scopes behave correctly"
)
def _():
    pass


@test("Suite.generate_test_runs correctly tears down module scoped parameterised tests")
def _():
    events = []

    @fixture(scope=Scope.Module)
    def a():
        events.append("resolve a")
        yield "a"
        events.append("teardown a")

    @testable_test
    def test_1(a=each(a, "second", a)):
        events.append("running test")

    suite = Suite(tests=[Test(fn=test_1, module_name="module1")])

    list(suite.generate_test_runs())

    # Ensure that each parameterised instance of the final test in the
    # module runs before the module-level teardown occurs.
    assert events == [
        "resolve a",
        "running test",
        "running test",
        "running test",
        "teardown a",
    ]


@test(
    "Suite.generate_test_runs fails an incorrectly parameterised test without expanding it"
)
def _():
    @testable_test
    def test_1(a=each(1, 2), b=each(1, 2, 3)):
        pass

    @testable_test
    def test_2(a=each(1, 2), b=each(1, 2)):
        pass

    suite = Suite(
        tests=[
            Test(fn=test_1, module_name="module1"),
            Test(fn=test_2, module_name="module2"),
        ]
    )

    results = list(suite.generate_test_runs())

    assert (
        len(results) == 1 + 2
    )  # the first test doesn't expand, and the 2nd test expands into 2 tests
    assert type(results[0].error) == ParameterisationError
