from ward import test


@test("[assert]")
def _():
    assert 1 == 2


@test("another")
def _():
    assert 5 == 9
