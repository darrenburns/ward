from unittest.mock import Mock

from ward import expect
from ward.fixtures import fixture
from ward.testing import Test, test, each


def f():
    expect(1).equals(1)


mod = "my_module"
t = Test(fn=f, module_name=mod)


@fixture
def anonymous_test():
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
    def parameterised_test(
        a=each(1,2,3),
        b="a value",
    ):
        pass

    t = Test(fn=parameterised_test, module_name=mod)

    expect(t.is_parameterised).equals(True)
