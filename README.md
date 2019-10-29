# Ward
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->[![All Contributors](https://img.shields.io/badge/all_contributors-2-orange.svg?style=flat-square)](#contributors-)<!-- ALL-CONTRIBUTORS-BADGE:END -->

![](https://github.com/darrenburns/ward/workflows/Ward%20CI/badge.svg)
[![PyPI version](https://badge.fury.io/py/ward.svg)](https://badge.fury.io/py/ward)

A modern Python test framework designed to help you find and fix flaws faster.

![screenshot](https://raw.githubusercontent.com/darrenburns/ward/master/screenshot.png)

## Features

This project is a work in progress. Some of the features that are currently available in a basic form are listed below.

* **Descriptive test names:** describe what your tests do using strings, not function names.
* **Modular test dependencies:** manage test setup/teardown code using fixtures that rely on Python's import system, not
name matching.
* **Powerful test selection:** limit your test run not only by matching test names/descriptions, but also on the code 
contained in the body of the test.
* **Colourful, human readable output:** quickly pinpoint and fix issues with detailed output for failing tests.
* **Expect API:** A simple but powerful assertion API inspired by [Jest](https://jestjs.io).
* **Cross platform:** Tested on Mac OS, Linux, and Windows.
* **Zero config:** Sensible defaults mean running `ward` with no arguments is enough to get started.

Planned features:

* Smart test execution order designed to surface failures faster (using various heuristics)
* Multi-process mode to improve performance
* Highly configurable output modes
* Code coverage with `--coverage` flag
* Handling flaky tests with test-specific retries, timeouts
* Integration with unittest.mock (specifics to be ironed out)
* Plugin system

## Getting Started

Install Ward with `pip install ward`.

Write your first test in `test_sum.py` (module name must start with `"test"`):

```python
from ward import expect, test

@test("1 plus 2 equals 3")
def _():
    expect(1 + 2).equals(3)
```

Now run your test with `ward` (no arguments needed). Ward will output the following:

```
 PASS  test_sum: 1 plus 2 equals 3
```

*You've just wrote your first test with Ward, congrats!* Look [here](#more-examples) for more examples.

## How to Contribute

Contributions are very welcome and encouraged!

See the [contributing guide](.github/CONTRIBUTING.md) for information on how you can take part in the development of Ward.

## More Examples

### Dependency injection with fixtures

In the example below, we define a single fixture named `city_list`.
We can supply this fixture as a default argument to a test, and Ward will resolve
it and inject the value into the test. Unlike pytest, Ward doesn't rely
on the parameter name matching the name of the fixture, and instead lets you make
use of Python's import machinery to specify which fixture you want to
inject.

```python
from ward import test, expect, fixture

@fixture
def city_list():
    return ["Glasgow", "Edinburgh"]
    
@test("'Glasgow' should be contained in the list of cities")
def _(cities=city_list):
    expect("Glasgow").contained_in(cities)
```

The fixture will be executed each time it gets injected into a test.

Fixtures are great for extracting common setup code that you'd otherwise need to repeat at the top of your tests, 
but they can also execute teardown code:

```python
from ward import test, expect, fixture

@fixture
def database():
    db_conn = setup_database()
    yield db_conn
    db_conn.close()


@test(f"Bob is one of the users contained in the database")
def _(db=database):
    # The database connection can be used in this test,
    # and will be closed after the test has completed.
    users = get_all_users(db)
    expect(users).contains("Bob")
```

The code below the `yield` statement in a fixture will be executed after the test runs. 

### Descriptive testing

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

### Test selection 

#### Search and run matching tests with `--search`

You can choose to limit which tests are collected and ran by Ward 
using the `--search STRING` option. Test names, descriptions *and test function bodies*
will be searched, and those which contain `STRING` will be ran. Here are
some examples:

**Run all tests that call the `fetch_users` function:**
```
ward --search "fetch_users("
```

**Run all tests that check if a `ZeroDivisionError` is raised:**
```
ward --search "raises(ZeroDivisionError)"
```

**Run all tests decorated with the `@xfail` decorator:**
```
ward --search "@xfail"
```

**To run a test called `test_the_sky_is_blue`:**

```text
ward --search test_the_sky_is_blue
```

**Running tests inside a module:**

The search takes place on the fully qualified name, so you can run a single
module (e.g. `my_module`) using the following command:

```text
ward --search my_module.
```

Of course, if a test name or body contains the string `"my_module."`, that test
will also be selected and ran. 

This approach is useful for quickly querying tests and running those which match a
simple query, making it useful for development.

Of course, sometimes you want to be very specific when declaring which tests to run.

#### Specific test selection

Ward will provide an option to query tests on name and description using substring
or regular expression matching.

(TODO)


### The `expect` API

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

### Working with mocks

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

### Checking for exceptions

The test below will pass, because a `ZeroDivisionError` is raised. If a `ZeroDivisionError` wasn't raised,
the test would fail.

```python
from ward import raises, test

@test("a ZeroDivision error is raised when we divide by 0")
def _():
    with raises(ZeroDivisionError):
        1/0
```

### Running tests in a directory

You can run tests in a specific directory using the `--path` option.
For example, to run all tests inside a directory called `tests`:

```text
ward --path tests
```

To run tests in the current directory, you can just type `ward`, which
is functionally equivalent to `ward --path .`

### Skipping a test

Use the `@skip` annotation to tell Ward not to execute a test.

```python
from ward import skip

@skip
def test_to_be_skipped():
    # ...
```

You can pass a `reason` to the `skip` decorator, and it will be printed
next to the test name/description during the run.

```python
@skip("not implemented yet")
@test("everything is okay")
def _():
    # ...
```

Here's the output Ward will print to the console when it runs the test above:

```
SKIP  test_things: everything is okay  [not implemented yet]
```

### Expecting a test to fail

You can mark a test that you expect to fail with the `@xfail` decorator. If a test
marked with this decorator passes unexpectedly, the overall run will be
considered a failure.

### Testing for approximate equality

Check that a value is close to another value.

```python
expect(1.0).approx(1.01, abs_tol=0.2)  # pass
expect(1.0).approx(1.01, abs_tol=0.001)  # fail
```

### Cancelling a run after a specific number of failures

If you wish for Ward to cancel a run immediately after a specific number of failing tests,
you can use the `--fail-limit` option. To have a run end immediately after 5 tests fail:

```text
ward --fail-limit 5
```

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://darrenburns.net"><img src="https://avatars0.githubusercontent.com/u/5740731?v=4" width="60px;" alt="Darren Burns"/><br /><sub><b>Darren Burns</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=darrenburns" title="Code">💻</a> <a href="https://github.com/darrenburns/ward/commits?author=darrenburns" title="Documentation">📖</a> <a href="#ideas-darrenburns" title="Ideas, Planning, & Feedback">🤔</a> <a href="#review-darrenburns" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/darrenburns/ward/issues?q=author%3Adarrenburns" title="Bug reports">🐛</a> <a href="#example-darrenburns" title="Examples">💡</a></td>
    <td align="center"><a href="https://github.com/khusrokarim"><img src="https://avatars0.githubusercontent.com/u/1615476?v=4" width="60px;" alt="khusrokarim"/><br /><sub><b>khusrokarim</b></sub></a><br /><a href="#ideas-khusrokarim" title="Ideas, Planning, & Feedback">🤔</a></td>
  </tr>
</table>

<!-- markdownlint-enable -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!