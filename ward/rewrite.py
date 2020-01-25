import ast
import inspect
import types
from typing import Iterable

from ward.expect import TestFailure, Operator
from ward.testing import Test


class RewriteAssert(ast.NodeTransformer):
    def visit_Assert(self, node):
        # Handle `assert x == y`
        if (
            isinstance(node.test, ast.Compare)
            and len(node.test.ops) == 1
            and isinstance(node.test.ops[0], ast.Eq)
        ):
            if node.msg and isinstance(node.msg, ast.Str):
                msg = node.msg.s
            else:
                msg = ""
            call = ast.Call(
                func=ast.Name(id="assert_equal", ctx=ast.Load()),
                args=[node.test.left, node.test.comparators[0], ast.Str(s=msg)],
                keywords=[],
            )

            new_node = ast.Expr(value=call)
            ast.copy_location(new_node, node)
            ast.fix_missing_locations(new_node)
            return new_node

        return node


def rewrite_assertions_in_tests(tests: Iterable[Test]):
    return [rewrite_assertion(test) for test in tests]


def assert_equal(lhs_val, rhs_val, assert_msg):
    if lhs_val != rhs_val:
        error_line_no = inspect.currentframe().f_back.f_lineno
        raise TestFailure(
            f"{lhs_val} != {rhs_val}",
            lhs=lhs_val,
            rhs=rhs_val,
            error_line=error_line_no,
            operator=Operator.Equals,
            assert_msg=assert_msg,
        )


def rewrite_assertion(test: Test) -> Test:
    # Get the old code and code object
    code = inspect.getsource(test.fn)
    code_obj = test.fn.__code__

    # Rewrite the AST of the code
    tree = ast.parse(code)
    line_no = inspect.getsourcelines(test.fn)[1]
    ast.increment_lineno(tree, line_no - 1)

    new_tree = RewriteAssert().visit(tree)

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
                {"assert_equal": assert_equal, **test.fn.__globals__, **clo_glob},
                test.fn.__name__,
                test.fn.__defaults__,
            )
            new_test_func.ward_meta = test.fn.ward_meta
            return Test(
                **{k: vars(test)[k] for k in vars(test) if k != "fn"}, fn=new_test_func,
            )

    return test
