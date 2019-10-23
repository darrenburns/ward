from ward import expect
from ward.test import skip, test


@skip
@test("adding 1 + 2 gives 3")
def _():
    expect(1 + 2).equals(3)


@test("adding 3 + 4 gives 7")
def _():
    expect(3 + 4).equals(8)
