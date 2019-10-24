from ward import test, expect, fixture
from ward.fixtures import FixtureRegistry, Fixture
from ward.testing import Test


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
    def _(a):
        expect(1).equals(1)

    return Test(fn=_, module_name=mod)


@fixture
def descriptive_test():
    @test("i have a description")
    def _():
        expect(1).equals(1)

    return Test(_, mod)


@test("Test.name should return the name of the function it wraps")
def _(anonymous_test):
    expect(anonymous_test.name).equals("_")


@test("Test.qualified_name should return `module_name.function_name`")
def _():
    expect(t.qualified_name).equals(f"{mod}.{f.__name__}")


@test("Test.qualified_name should return `module_name._` when test name is _")
def _(anonymous_test):
    expect(anonymous_test.qualified_name).equals(f"{mod}._")


@test("Test.deps should return {} when test uses no fixtures")
def _(anonymous_test):
    expect(anonymous_test.deps()).equals({})


@test("Test.deps should return correct params when test uses fixtures")
def _(dependent_test):
    deps = dependent_test.deps()
    expect(deps).contains("a")


@test("Test.has_deps should return True when test uses fixtures")
def _(dependent_test):
    expect(dependent_test.has_deps()).equals(True)


@test("Test.has_deps should return False when test doesn't use fixtures")
def _(anonymous_test):
    expect(anonymous_test.has_deps()).equals(False)


@test("Test.resolve_args should return {} when test doesn't use fixtures")
def _(anonymous_test):
    expect(anonymous_test.resolve_args(FixtureRegistry())).equals({})


@test("Test.resolve_args should return a map of param names to resolved Fixture")
def _():
    reg = FixtureRegistry()
    val = 1
    fixture = Fixture("my_fixture", lambda: val)
    reg.cache_fixture(fixture)
    test = Test(lambda my_fixture: 1, "module_name")

    expect(test.resolve_args(reg)).equals({"my_fixture": fixture})
    expect(fixture.resolved_val).equals(val)
