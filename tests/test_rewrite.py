from tests.test_suite import testable_test
from ward import test, fixture, raises
from ward.expect import TestFailure
from ward.rewrite import assert_equal, rewrite_assertions_in_tests
from ward.testing import Test


@testable_test
def passing_fn():
    assert True


@testable_test
def failing_fn():
    assert False


@fixture
def passing():
    yield Test(
        fn=passing_fn, module_name="m", id="id-pass",
    )


@fixture
def failing():
    yield Test(
        fn=failing_fn, module_name="m", id="id-fail",
    )


@test("assert_equal doesnt raise if lhs == rhs")
def _():
    assert_equal(1, 1, "")


@test("assert_equal raises TestFailure if lhs != rhs")
def _():
    with raises(TestFailure):
        assert_equal(1, 2, "")


@test("rewrite_assertions_in_tests returns all tests, keeping metadata")
def _(p=passing, f=failing):
    in_tests = [p, f]
    out_tests = rewrite_assertions_in_tests(in_tests)
    assert [(test.description, test.id, test.module_name) for test in in_tests] == [
        (test.description, test.id, test.module_name) for test in out_tests
    ]
