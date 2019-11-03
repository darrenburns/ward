---
title: "Tutorial: Your first tests"
path: "/guide/tutorial"
section: "user guide"
---

Ward is available on [PyPI](https://pypi.org/project/ward/), meaning it can be installed using `pip`.

```
pip install ward
```

When you run `ward` with no arguments, it will recursively look for tests starting from your current directory.

Ward will look for tests in any Python file with a name that starts with `test_`.

We're going to write tests for a function called `contains`, shown below.

```python
def contains(list_of_items, target_item):
    for current_item in list_of_items:
        if current_item == target_item:
            return True
    return False
```

This function should return `True`, if the `item` is contained within a list. Otherwise it should return `False`.

## Our first test

Tests in ward are just Python functions annotated with the `@test(description: str)` decorator.

Functions annotated with this decorator can be named `_`. We'll tell readers
 what the test does using a plain English description rather than the function name.

Our test is contained within a file called `test_contains.py`:

```python
from contains import contains
from ward import expect, test

@test("contains returns True when item is in list")
def _():
    list_of_items = list(range(10))
    result = contains(list_of_items, 5)
    expect(result).equals(True)
```

In this file, we've defined a single test function called `_`. It's been
annotated as a test using `@test`, and has a helpful description. We don't have to read the code inside the test to 
understand its purpose.

The description can be queried when running a subset of 
tests. You may decide to use your own conventions inside the description
in order to make your tests highly queryable.

To run the test, just run `ward` in your terminal.

## Extracting common setup code

Lets add another test.

```python
@test("contains returns False when item is not in list")
def _():
    list_of_items = list(range(100000))
    result = contains(list_of_items, -1)
    expect(result).equals(False)
```

This test begins by instantiating the same list of 10 integers as the first
test. This duplicated setup code can be extracted out into a *fixture* so that we
don't have to repeat ourselves at the start of every test.

The `@fixture` decorator lets us define a fixture, which is a unit of test setup code. It can optionally contain some additional code to clean up any resources
the fixture used (e.g. cleaning up a test database).

Lets define a fixture immediately above the tests we just wrote.

```python
from ward import fixture

@fixture
def list_of_items():
    return list(range(100000))
```

We can now rewrite our tests to make use of this fixture. Here's how we'd rewrite the second test to use the fixture.

```python
@test("contains returns False when item is not in list")
def _(l=list_of_items):
    result = contains(l, -1)
    expect(result).equals(False)
```

By binding the name of the fixture as a default argument to the test, Ward will
resolve the value of the fixture before the test runs, and inject it into the test. 

By default, a fixture is executed immediately before being injected into
a test. In the case of this fixture, that could be problematic if lots of tests
depend on it. Do we really want to instantiate a list of 100000 integers before
each of those tests? Probably not.

To avoid this repeated expensive test setup, you can tell Ward what the *scope* of a fixture is. The scope of a fixture defines how long it should be cached for.

Ward supports 3 scopes: `test` (default), `module`, and `global`.

* A `test` scoped fixture will be executed at most once per test.
* A `module` scoped fixture will be executed at most once per module.
* A `global` scoped fixture will be executed at most once per invocation of `ward`.

We can safely say that we only need to generate our `list_of_items` fixture once, and we can reuse its value in every test that depends on it. So lets give it a `global` scope:

```python
from ward import Scope

@fixture(scope=Scope.Global)  # or scope="global"
def list_of_items():
    return list(range(100000))
```

With this change, our fixture will now only be executed once, regardless of how
many tests depend on it.

TODO: Note on read-only fixtures and scoping
