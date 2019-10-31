---
title: "Writing tests"
path: "/writing-tests"
---

## Descriptive testing

Test frameworks usually require that you describe how your tests work using
a function name. As a result test names are often short and non-descriptive,
or long and unreadable.

Ward lets you describe your tests using strings, meaning you can be as descriptive
as you'd like:

```python
from ward import expect, test

NAME = "Win Butler"

@test("my_sum(1, 2) is equal to 3")
def _():
    total = my_sum(1, 2)
    expect(total).equals(3)
    
@test(f"first_char('{NAME}') returns '{NAME[0]}'")
def _():
    first_char = first_char(NAME)
    expect(first_char).equals(NAME[0])
```

During the test run, Ward will print the descriptive test name to the console:

```
FAIL  test_things: my_sum(1, 2) is equal to 3
PASS  test_things: first_char('Win Butler') returns 'W'
```

If you'd still prefer to name your tests using function names, you can do so
by starting the name of your test function with `test_`:

```python
def test_my_sum_returns_the_sum_of_the_input_numbers():
    total = my_sum(1, 2)
    expect(total).equals(3)
```

## The `expect` API

Use `expect` to perform tests on objects by chaining together methods. Using `expect` allows Ward
to provide detailed, highly readable output when your tests fail. 

```python
from ward import expect, fixture

@fixture
def cities():
    return {"edinburgh": "scotland", "tokyo": "japan", "madrid": "spain"}

def test_capital_cities(cities=cities):
    found_cities = get_capitals_from_server()

    (expect(found_cities)
     .contains("tokyo")                                 # it contains the key 'tokyo'
     .satisfies(lambda x: all(len(k) < 10 for k in x))  # all keys < 10 chars
     .equals(cities))
```

Most methods on `expect` have inverted equivalents, e.g. `not_equals`, `not_satisfies`, etc.

## Working with mocks

`expect` works well with `unittest.mock`, by providing methods such as `expect.called`, `expect.called_once_with`, 
and more. If a test fails due to the mock not being used as expected, Ward will print specialised output to aid
debugging the problem.

```python
from ward import test, expect
from unittest.mock import Mock

@test("the mock was called with the expected arguments")
def _():
    mock = Mock()
    mock(1, 2, x=3)
    expect(mock).called_once_with(1, 2, x=3)
```

## Checking for exceptions

The test below will pass, because a `ZeroDivisionError` is raised. If a `ZeroDivisionError` wasn't raised,
the test would fail.

```python
from ward import raises, test

@test("a ZeroDivision error is raised when we divide by 0")
def _():
    with raises(ZeroDivisionError):
        1/0
```

## Expecting a test to fail

You can mark a test that you expect to fail with the `@xfail` decorator. If a test
marked with this decorator passes unexpectedly, the overall run will be
considered a failure.

## Testing for approximate equality

Check that a value is close to another value.

```python
expect(1.0).approx(1.01, abs_tol=0.2)  # pass
expect(1.0).approx(1.01, abs_tol=0.001)  # fail
```