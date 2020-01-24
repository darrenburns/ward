from ward import test, using, fixture


@fixture
def darren():
    return "darren"


@using(name=darren)
@test("assert statements give full diff with @using")
def _(name):
    assert "darren" == name


@test("assert statements give full diff without @using")
def _(name=darren):
    assert "darren" == name
