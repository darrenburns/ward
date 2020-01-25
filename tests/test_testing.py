from unittest import mock
from unittest.mock import Mock

from tests.test_suite import testable_test
from ward import raises, Scope
from ward.errors import ParameterisationError
from ward.fixtures import fixture
from ward.testing import Test, test, each, ParamMeta


def f():
    assert 1 == 1


mod = "my_module"
t = Test(fn=f, module_name=mod)


@fixture
def anonymous_test():
    @testable_test
    def _():
        assert 1 == 1

    return Test(fn=_, module_name=mod)


@fixture
def dependent_test():
    def x():
        return 1

    def _(a=x):
        assert 1 == 1

    return Test(fn=_, module_name=mod)


@test("Test.name should return the name of the function it wraps")
def _(anonymous_test=anonymous_test):
    assert anonymous_test.name == "_"


@test("dict comparison")
def _():
    left = {"brand": "Ford", "model": "Mustang", "year": 1964}
    right = {"brand": "Toyota", "model": "Mustang", "year": 2001}

    assert left == right


@test("Test.qualified_name should return `module_name.function_name`")
def _():
    assert t.qualified_name == f"{mod}.{f.__name__}"


@test("Test.qualified_name should return `module_name._` when test name is _")
def _(anonymous_test=anonymous_test):
    assert anonymous_test.qualified_name == f"{mod}._"


@test("Test.deps should return {} when test uses no fixtures")
def _(anonymous_test=anonymous_test):
    assert anonymous_test.deps() == {}


@test("Test.deps should return correct params when test uses fixtures")
def _(dependent_test=dependent_test):
    deps = dependent_test.deps()
    assert "a" in deps


@test("Test.has_deps should return True when test uses fixtures")
def _(dependent_test=dependent_test):
    assert dependent_test.has_deps


@test("Test.has_deps should return False when test doesn't use fixtures")
def _(anonymous_test=anonymous_test):
    assert not anonymous_test.has_deps


@test("Test.__call__ should delegate to the function it wraps")
def _():
    mock = Mock()
    t = Test(fn=mock, module_name=mod)
    t(1, 2, key="val")
    mock.assert_called_once_with(1, 2, key="val")


@test("Test.is_parameterised should return True for parameterised test")
def _():
    def parameterised_test(a=each(1, 2, 3), b="a value"):
        pass

    t = Test(fn=parameterised_test, module_name=mod)

    assert t.is_parameterised == True


@test("Test.is_parameterised should return False for standard tests")
def _():
    def test():
        pass

    t = Test(fn=test, module_name=mod)

    assert not t.is_parameterised


@test("Test.scope_key_from(Scope.Test) returns the test ID")
def _(t: Test = anonymous_test):
    scope_key = t.scope_key_from(Scope.Test)

    assert scope_key == t.id


@test("Test.scope_key_from(Scope.Module) returns the path of the test module")
def _(t: Test = anonymous_test):
    scope_key = t.scope_key_from(Scope.Module)

    assert scope_key == testable_test.path


@test("Test.scope_key_from(Scope.Global) returns Scope.Global")
def _(t: Test = anonymous_test):
    scope_key = t.scope_key_from(Scope.Global)

    assert scope_key == Scope.Global


@test("Test.get_parameterised_instances returns [self] if not parameterised")
def _():
    def test():
        pass

    t = Test(fn=test, module_name=mod)

    assert t.get_parameterised_instances() == [t]


@test("Test.get_parameterised_instances returns correct number of test instances")
def _():
    def test(a=each(1, 2), b=each(3, 4)):
        pass

    t = Test(fn=test, module_name=mod)
    assert t.get_parameterised_instances() == [
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


@test("Test.get_parameterised_instances raises exception for arg count mismatch")
def _():
    def invalid_test(a=each(1, 2), b=each(3, 4, 5)):
        pass

    t = Test(fn=invalid_test, module_name=mod)

    with raises(ParameterisationError):
        t.get_parameterised_instances()
