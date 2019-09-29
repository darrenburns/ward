# Ward

An experimental test runner for Python 3.6+ that is heavily inspired by `pytest`. This project is a work in progress, and is not production ready.

![screenshot](https://raw.githubusercontent.com/darrenburns/ward/master/screenshot.png)

## Examples

### Dependency Injection

In the example below, we define a single fixture named `cities`.
Our test takes a single parameter, which is also named `cities`.
Ward sees that the fixture name and parameter names match, so it
calls the `cities` fixture, and passes the result into the test.

```python
from ward.fixtures import fixture

@fixture
def cities():
    return ["Glasgow", "Edinburgh"]
    
def test_using_cities(cities):
    assert cities == ["Glasgow", "Edinburgh"]
```

### The Expect API

In the (contrived) `test_capital_cities` test, we want to determine whether
the `get_capitals_from_server` function is behaving as expected, 
so we grab the output of the function and pass it to `expect`. From
here, we check that the response is as we expect it to be by chaining
methods. If any of the checks fail, the expect chain short-circuits,
and the remaining checks won't be executed for that test. Methods in
the Expect API are named such that they correspond as closely to standard
Python operators as possible, meaning there's not much to memorise.

```python
from ward.fixtures import fixture
from ward.expect import expect

@fixture
def cities():
    return {"edinburgh": "scotland", "tokyo": "japan", "london": "england", "warsaw": "poland", "berlin": "germany",
            "madrid": "spain"}

def test_capital_cities(cities):
    found_cities = get_capitals_from_server()

    (expect(found_cities)
     .contains("tokyo")  # it contains the key 'tokyo'
     .satisfies(lambda x: all(len(k) < 10 for k in x))  # all keys < 10 chars
     .equals(cities))
```

### Checking for exceptions

The test below will pass, because a `ZeroDivisionError` is raised. If a `ZeroDivisionError` wasn't raised,
the test would fail.

```python
from ward.expect import raises

def test_expecting_an_exception():
    with raises(ZeroDivisionError):
        1/0
```


