import ast

from tests.test_suite import testable_test
from ward import test, fixture, raises
from ward.expect import TestFailure
from ward.rewrite import assert_equal, rewrite_assertions_in_tests, RewriteAssert
from ward.testing import Test


@testable_test
def passing_fn():
    assert 1 == 1


@testable_test
def failing_fn():
    assert 1 == 2


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

    def meta(test):
        return (test.description, test.id, test.module_name, test.fn.ward_meta)

    assert [meta(test) for test in in_tests] == [meta(test) for test in out_tests]


@test("RewriteAssert.visit_Assert doesn't touch `assert x`")
def _():
    src = "assert False"
    in_tree = ast.parse(src).body[0]
    out_tree = RewriteAssert().visit(in_tree)
    assert in_tree == out_tree


@test("RewriteAssert.visit_Assert transforms `assert x == y`")
def _():
    src = "assert 1 == 2"
    in_tree = ast.parse(src).body[0]
    out_tree = RewriteAssert().visit(in_tree)

    assert out_tree.lineno == in_tree.lineno
    assert out_tree.col_offset == in_tree.col_offset
    assert out_tree.value.lineno == in_tree.lineno
    assert out_tree.value.col_offset == in_tree.col_offset
    assert out_tree.value.func.id == "assert_equal"
    assert out_tree.value.args[0].n == 1
    assert out_tree.value.args[1].n == 2
    assert out_tree.value.args[2].s == ''
