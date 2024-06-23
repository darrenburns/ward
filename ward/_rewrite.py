import ast
import inspect
import sys
import textwrap
import types
from pathlib import Path
from typing import Iterable, List

from ward.expect import (
    assert_equal,
    assert_greater_than,
    assert_greater_than_equal_to,
    assert_in,
    assert_is,
    assert_is_not,
    assert_less_than,
    assert_less_than_equal_to,
    assert_not_equal,
    assert_not_in,
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


def get_assertion_msg(assertion: ast.Assert) -> ast.expr:
    if assertion.msg:
        return assertion.msg
    else:
        return ast.Str("")


def make_call_node(node: ast.expr, func_name: str) -> ast.Expr:
    call = ast.Call(
        func=ast.Name(id=func_name, ctx=ast.Load()),
        args=[node.test.left, node.test.comparators[0], get_assertion_msg(node)],
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
    def visit_Assert(self, node):  # noqa: C901 - no chance to reduce complexity
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


def exec_module(module: types.ModuleType):
    filename = module.__spec__.origin
    code = module.__loader__.get_source(module.__name__)
    tree = ast.parse(code, filename=filename)
    new_tree = RewriteAssert().visit(tree)
    code = compile(new_tree, filename, "exec", dont_inherit=True)
    module.__dict__.update(assert_func_namespace)
    exec(code, module.__dict__)
