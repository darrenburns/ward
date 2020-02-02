import ast
import inspect
import textwrap
import types
from typing import Iterable, List

from ward.expect import (
    assert_equal,
    assert_not_equal,
    assert_in,
    assert_not_in,
    assert_is,
    assert_is_not,
    assert_less_than_equal_to,
    assert_less_than,
    assert_greater_than_equal_to,
    assert_greater_than,
)
from ward.testing import Test

assert_func_namespace = {
    assert_equal.__name__: assert_equal,
    assert_not_equal.__name__: assert_not_equal,
    assert_in.__name__: assert_in,
    assert_not_in.__name__: assert_not_in,
    assert_is.__name__: assert_is,
    assert_is_not.__name__: assert_is_not,
    assert_less_than_equal_to.__name__: assert_less_than_equal_to,
    assert_less_than.__name__: assert_less_than,
    assert_greater_than_equal_to.__name__: assert_greater_than_equal_to,
    assert_greater_than.__name__: assert_greater_than,
}


def get_assertion_msg(node: ast.expr) -> str:
    if node.msg and isinstance(node.msg, ast.Str):
        msg = node.msg.s
    else:
        msg = ""
    return msg


def make_call_node(node: ast.expr, func_name: str) -> ast.Expr:
    msg = get_assertion_msg(node)
    call = ast.Call(
        func=ast.Name(id=func_name, ctx=ast.Load()),
        args=[node.test.left, node.test.comparators[0], ast.Str(s=msg)],
        keywords=[],
    )
    new_node = ast.Expr(value=call)
    ast.copy_location(new_node, node)
    ast.fix_missing_locations(new_node)
    return new_node


def is_binary_comparison(node: ast.expr) -> bool:
    return isinstance(node.test, ast.Compare) and len(node.test.ops) == 1


def is_comparison_type(node: ast.expr, type) -> bool:
    return isinstance(node.test.ops[0], type)


class RewriteAssert(ast.NodeTransformer):
    def visit_Assert(self, node):
        if is_binary_comparison(node):
            if is_comparison_type(node, ast.Eq):
                return make_call_node(node, assert_equal.__name__)
            elif is_comparison_type(node, ast.NotEq):
                return make_call_node(node, assert_not_equal.__name__)
            elif is_comparison_type(node, ast.In):
                return make_call_node(node, assert_in.__name__)
            elif is_comparison_type(node, ast.NotIn):
                return make_call_node(node, assert_not_in.__name__)
            elif is_comparison_type(node, ast.Is):
                return make_call_node(node, assert_is.__name__)
            elif is_comparison_type(node, ast.IsNot):
                return make_call_node(node, assert_is_not.__name__)
            elif is_comparison_type(node, ast.Lt):
                return make_call_node(node, assert_less_than.__name__)
            elif is_comparison_type(node, ast.LtE):
                return make_call_node(node, assert_less_than_equal_to.__name__)
            elif is_comparison_type(node, ast.Gt):
                return make_call_node(node, assert_greater_than.__name__)
            elif is_comparison_type(node, ast.GtE):
                return make_call_node(node, assert_greater_than_equal_to.__name__)

        return node


def rewrite_assertions_in_tests(tests: Iterable[Test]) -> List[Test]:
    return [rewrite_assertion(test) for test in tests]


def rewrite_assertion(test: Test) -> Test:
    # Get the old code and code object
    code = inspect.getsource(test.fn)
    indents = textwrap._leading_whitespace_re.findall(code)
    col_offset = len(indents[0]) if len(indents) > 0 else 0
    code = textwrap.dedent(code)
    code_obj = test.fn.__code__

    # Rewrite the AST of the code
    tree = ast.parse(code)
    line_no = inspect.getsourcelines(test.fn)[1]
    ast.increment_lineno(tree, line_no - 1)

    new_tree = RewriteAssert().visit(tree)

    # We dedented the code so that it was a valid tree, now re-apply the indent
    for child in ast.walk(new_tree):
        if hasattr(child, "col_offset"):
            child.col_offset = getattr(child, "col_offset", 0) + col_offset

    # Reconstruct the test function
    new_mod_code_obj = compile(new_tree, code_obj.co_filename, "exec")

    # TODO: This probably isn't correct for nested closures
    clo_glob = {}
    if test.fn.__closure__:
        clo_glob = test.fn.__closure__[0].cell_contents.__globals__

    for const in new_mod_code_obj.co_consts:
        if isinstance(const, types.CodeType):
            new_test_func = types.FunctionType(
                const,
                {**assert_func_namespace, **test.fn.__globals__, **clo_glob},
                test.fn.__name__,
                test.fn.__defaults__,
            )
            new_test_func.ward_meta = test.fn.ward_meta
            return Test(
                **{k: vars(test)[k] for k in vars(test) if k != "fn"}, fn=new_test_func,
            )

    return test
