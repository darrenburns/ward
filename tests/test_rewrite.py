import ast

from tests.utilities import testable_test, failing_assertion
from ward import fixture, test
from ward._rewrite import (
    RewriteAssert,
    get_assertion_msg,
    is_binary_comparison,
    is_comparison_type,
    make_call_node,
)
from ward.expect import TestAssertionFailure, raises
from ward.testing import Test, each


def as_dict(node):
    if isinstance(node, ast.AST):
        d = {
            k: as_dict(v)
            for k, v in vars(node).items()
            if k
            not in {
                "lineno",
                "col_offset",
                "ctx",
                "end_lineno",
                "end_col_offset",
                "kind",
            }
        }
        d["_type"] = type(node)
        return d
    else:
        return node


@test("RewriteAssert.visit_Assert doesn't transform `{src}`")
def _(
    src=each(
        "assert x",
        "assert f(x)",
        "assert x + y + z",
        "assert 1 < 2 < 3",
        "assert 1 == 1 == 3",
        "print(x)",
        "yield",
    )
):
    in_tree = ast.parse(src).body[0]
    out_tree = RewriteAssert().visit(in_tree)
    assert in_tree == out_tree


@test("RewriteAssert.visit_Assert transforms `{src}` correctly")
def _(
    src=each(
        "assert x == y",
        "assert x != y",
        "assert x in y",
        "assert x not in y",
        "assert x is y",
        "assert x is not y",
        "assert x < y",
        "assert x <= y",
        "assert x > y",
        "assert x >= y",
    ),
    fn=each(
        "assert_equal",
        "assert_not_equal",
        "assert_in",
        "assert_not_in",
        "assert_is",
        "assert_is_not",
        "assert_less_than",
        "assert_less_than_equal_to",
        "assert_greater_than",
        "assert_greater_than_equal_to",
    ),
):
    in_tree = ast.parse(src).body[0]
    out_tree = RewriteAssert().visit(in_tree)

    assert out_tree.lineno == in_tree.lineno
    assert out_tree.col_offset == in_tree.col_offset
    assert out_tree.value.lineno == in_tree.lineno
    assert out_tree.value.col_offset == in_tree.col_offset
    assert out_tree.value.func.id == fn
    assert out_tree.value.args[0].id == "x"
    assert out_tree.value.args[1].id == "y"
    assert out_tree.value.args[2].s == ""

@test("This test suite's assertions are themselves rewritten")
def _():
    with raises(TestAssertionFailure):
        assert 1 == 2
    with raises(TestAssertionFailure):
        assert 1 != 1
    with raises(TestAssertionFailure):
        assert 1 in ()
    with raises(TestAssertionFailure):
        assert 1 not in (1,)
    with raises(TestAssertionFailure):
        assert None is Ellipsis
    with raises(TestAssertionFailure):
        assert None is not None
    with raises(TestAssertionFailure):
        assert 2 < 1
    with raises(TestAssertionFailure):
        assert 2 <= 1
    with raises(TestAssertionFailure):
        assert 1 > 2
    with raises(TestAssertionFailure):
        assert 1 >= 2

@test("Non-test modules' assertions aren't rewritten")
def _():
    with raises(AssertionError):
        failing_assertion()

@test("RewriteAssert.visit_Assert transforms `{src}`")
def _(src="assert 1 == 2, 'msg'"):
    in_tree = ast.parse(src).body[0]
    out_tree = RewriteAssert().visit(in_tree)
    assert out_tree.value.args[2].s == "msg"


for msg, expected in [
    ("", ast.Str("")),
    (", 'msg'", ast.Str("msg")),
    (", 1", ast.Num(1)),
    (", 1 + 1", ast.BinOp(ast.Num(1), ast.Add(), ast.Num(1))),
    (", 1 - 1", ast.BinOp(ast.Num(1), ast.Sub(), ast.Num(1))),
]:

    @test("get_assertion_message({src}) returns '{msg}'")
    def _(msg=msg, expected=expected):
        in_tree: ast.Assert = ast.parse(f"assert 1 == 2{msg}").body[0]
        from_source = get_assertion_msg(in_tree)
        assert as_dict(from_source) == as_dict(expected)


@test("make_call_node converts `{src}` to correct function call node`")
def _(
    src=each(
        "assert x == y",
        "assert x == y, 'message'",
        "assert x < y",
        "assert x in y",
        "assert x is y",
        "assert x is not y",
    ),
    func="my_assert",
):
    assert_node = ast.parse(src).body[0]
    call = make_call_node(assert_node, func)

    # check that `assert x OP y` becomes `my_assert(x, y, '')`
    lhs = assert_node.test.left.id
    rhs = assert_node.test.comparators[0].id
    msg = assert_node.msg.s if assert_node.msg else ""

    assert call.value.args[0].id == lhs
    assert call.value.args[1].id == rhs
    assert call.value.args[2].s == msg


@test("is_binary_comparison returns True for assert binary comparisons")
def _(src=each("assert x == y", "assert x is y", "assert x < y", "assert x is not y")):
    assert_node = ast.parse(src).body[0]
    assert is_binary_comparison(assert_node)


@test("is_binary_comparison('{src}') is False")
def _(src=each("assert True", "assert x < y < z", "assert not False")):
    assert_node = ast.parse(src).body[0]
    assert not is_binary_comparison(assert_node)


@test("is_comparison_type returns True if node is of given type")
def _(
    src=each("assert x == y", "assert x is y", "assert x < y", "assert x is not y"),
    node_type=each(ast.Eq, ast.Is, ast.Lt, ast.IsNot),
):
    assert_node = ast.parse(src).body[0]
    assert is_comparison_type(assert_node, node_type)


@test("is_comparison_type returns False if node is not of given type")
def _(
    src=each("assert x == y", "assert x is y", "assert x < y", "assert x is not y"),
    node_type=each(ast.Add, ast.Add, ast.Add, ast.Add),
):
    assert_node = ast.parse(src).body[0]
    assert not is_comparison_type(assert_node, node_type)


if True:

    @test("test with indentation level of 1")
    def _():
        assert 1 + 2 == 3

    if True:

        @test("test with indentation level of 2")
        def _():
            assert 2 + 3 == 5
