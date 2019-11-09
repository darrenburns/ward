from unittest import mock
from unittest.mock import Mock

from tests.test_suite import testable_test
from ward import expect, raises, Scope
from ward.errors import ParameterisationError
from ward.fixtures import fixture
from ward.testing import Test, test, each, ParamMeta


def f():
    expect(1).equals(1)


mod = "my_module"
t = Test(fn=f, module_name=mod)


@fixture
def anonymous_test():
    @testable_test
    def _():
        expect(1).equals(1)

    return Test(fn=_, module_name=mod)


@fixture
def dependent_test():
    def x():
        return 1

    def _(a=x):
        expect(1).equals(1)

    return Test(fn=_, module_name=mod)


@test("Test.name should return the name of the function it wraps")
def _(anonymous_test=anonymous_test):
    expect(anonymous_test.name).equals("_")


@test("Test.qualified_name should return `module_name.function_name`")
def _():
    expect(t.qualified_name).equals(f"{mod}.{f.__name__}")


@test("Test.qualified_name should return `module_name._` when test name is _")
def _(anonymous_test=anonymous_test):
    expect(anonymous_test.qualified_name).equals(f"{mod}._")


@test("Test.deps should return {} when test uses no fixtures")
def _(anonymous_test=anonymous_test):
    expect(anonymous_test.deps()).equals({})


@test("Test.deps should return correct params when test uses fixtures")
def _(dependent_test=dependent_test):
    deps = dependent_test.deps()
    expect(deps).contains("a")


@test("Test.has_deps should return True when test uses fixtures")
def _(dependent_test=dependent_test):
    expect(dependent_test.has_deps).equals(True)


@test("Test.has_deps should return False when test doesn't use fixtures")
def _(anonymous_test=anonymous_test):
    expect(anonymous_test.has_deps).equals(False)


@test("Test.__call__ should delegate to the function it wraps")
def _():
    mock = Mock()
    t = Test(fn=mock, module_name=mod)
    t(1, 2, key="val")
    expect(mock).called_once_with(1, 2, key="val")


@test("Test.is_parameterised should return True for parameterised test")
def _():
    def parameterised_test(a=each(1, 2, 3), b="a value"):
        pass

    t = Test(fn=parameterised_test, module_name=mod)

    expect(t.is_parameterised).equals(True)


@test("Test.is_parameterised should return False for standard tests")
def _():
    def test():
        pass

    t = Test(fn=test, module_name=mod)

    expect(t.is_parameterised).equals(False)


@test("Test.scope_key_from(Scope.Test) returns the test ID")
def _(t: Test = anonymous_test):
    scope_key = t.scope_key_from(Scope.Test)

    expect(scope_key).equals(t.id)


@test("Test.scope_key_from(Scope.Module) returns the path of the test module")
def _(t: Test = anonymous_test):
    scope_key = t.scope_key_from(Scope.Module)

    expect(scope_key).equals(testable_test.path)


@test("Test.scope_key_from(Scope.Global) returns Scope.Global")
def _(t: Test = anonymous_test):
    scope_key = t.scope_key_from(Scope.Global)

    expect(scope_key).equals(Scope.Global)


@test("Test.get_parameterised_instances returns [self] if not parameterised")
def _():
    def test():
        pass

    t = Test(fn=test, module_name=mod)

    expect(t.get_parameterised_instances()).equals([t])


@test("Test.get_parameterised_instances returns correct number of test instances")
def _():
    def test(a=each(1, 2), b=each(3, 4)):
        pass

    t = Test(fn=test, module_name=mod)
    expect(t.get_parameterised_instances()).equals(
        [
            Test(
                id=mock.ANY,
                fn=t.fn,
                module_name=t.module_name,
                param_meta=ParamMeta(0, 2),
                sout=mock.ANY,
                serr=mock.ANY,
            ),
            Test(
                id=mock.ANY,
                fn=t.fn,
                module_name=t.module_name,
                param_meta=ParamMeta(1, 2),
                sout=mock.ANY,
                serr=mock.ANY,
            ),
        ]
    )


@test("Test.get_parameterised_instances raises exception for arg count mismatch")
def _():
    def invalid_test(a=each(1, 2), b=each(3, 4, 5)):
        pass

    t = Test(fn=invalid_test, module_name=mod)

    with raises(ParameterisationError):
        t.get_parameterised_instances()
