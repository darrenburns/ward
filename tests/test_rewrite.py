from tests.test_suite import testable_test
from ward import test, fixture, raises
from ward.expect import TestFailure
from ward.rewrite import assert_equal
from ward.testing import Test


@testable_test
def passing_fn():
    assert 1 == 1


@fixture
def passing():
    yield Test(
        fn=passing_fn,
        module_name="m",
        id="id",
    )


@test("assert_equal doesnt raise if lhs == rhs")
def _():
    assert_equal(1, 1, "")


@test("assert_equal raises TestFailure if lhs != rhs")
def _():
    with raises(TestFailure):
        assert_equal(1, 2, "")
