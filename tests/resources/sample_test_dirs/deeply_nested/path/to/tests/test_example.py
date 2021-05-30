# Ensure that if we import a test from another test module
# that we don't run the tests in that module two times!
from test_another_example import *


@test("two is equal to itself")
def _():
    assert 2 == 2
