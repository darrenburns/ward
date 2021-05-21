from tests.utilities import dummy_fixture
from ward import each, test
from ward.fixtures import Fixture
from ward.testing import Test


@test("Resolver identifies arguments that are fixtures for unparameterised test")
def _():
    def foo(fixture=dummy_fixture, not_fixture=5):
        pass

    t = Test(foo, module_name="")

    assert t.resolver.fixtures == {"fixture": Fixture(dummy_fixture)}


@test("Resolver identifies arguments that are fixtures for parameterised test")
def _():
    def foo(
        a=each(dummy_fixture, "foo", dummy_fixture, "fourth"),
        b=each("bar", dummy_fixture, dummy_fixture, "fourth"),
    ):
        pass

    t = Test(foo, module_name="")

    first, second, third, fourth = t.get_parameterised_instances()

    assert first.resolver.fixtures == {"a": Fixture(dummy_fixture)}
    assert second.resolver.fixtures == {"b": Fixture(dummy_fixture)}
    assert third.resolver.fixtures == {
        "a": Fixture(dummy_fixture),
        "b": Fixture(dummy_fixture),
    }
    assert fourth.resolver.fixtures == {}
