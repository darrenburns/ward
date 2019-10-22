# Ward
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->[![All Contributors](https://img.shields.io/badge/all_contributors-2-orange.svg?style=flat-square)](#contributors-)<!-- ALL-CONTRIBUTORS-BADGE:END -->

![](https://github.com/darrenburns/ward/workflows/Ward%20CI/badge.svg)

A modern Python test framework designed to help you find and fix flaws faster.

![screenshot](https://raw.githubusercontent.com/darrenburns/ward/master/screenshot.png)

## Features

This project is a work in progress. Some of the features that are currently available in a basic form are listed below.

* **Colourful, human readable output:** quickly pinpoint and fix issues with detailed output for failing tests.
* **Modular test dependencies:** manage test setup/teardown code using modular pytest-style fixtures.
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
re
## Getting Started

Install Ward with `pip install ward`.

Write your first test in `test_sum.py` (module name must start with `"test"`):

```python
from ward import expect

def test_one_plus_two_equals_three():  # name must start with "test"
    expect(1 + 2).equals(3)
```

Now run your test with `ward` (no arguments needed). Ward will output the following:

```
 PASS  test_sum.test_one_plus_two_equals_three
```

*You've just wrote your first test with Ward, congrats!* Look [here](#more-examples) for more examples of
how to test things with Ward.

## How to Contribute

Contributions are very welcome and encouraged!

See the [contributing guide](.github/CONTRIBUTING.md) for information on how you can take part in the development of Ward.

## More Examples

### Dependency injection with fixtures

In the example below, we define a single fixture named `cities`.
Our test takes a single parameter, which is also named `cities`.
Ward sees that the fixture name and parameter names match, so it
calls the `cities` fixture, and passes the result into the test.

```python
from ward import expect, fixture

@fixture
def cities():
    return ["Glasgow", "Edinburgh"]
    
def test_using_cities(cities):
    expect(cities).equals(["Glasgow", "Edinburgh"])
```

Fixtures are great for extracting common setup code that you'd otherwise need to repeat at the top of your tests, 
but they can also execute teardown code:

```python
@fixture
def database():
    db_conn = setup_database()
    yield db_conn
    db_conn.close()


def test_database_connection(database):
    # The database connection can be used in this test,
    # and will be closed after the test has completed.
    users = get_all_users(database)
    expect(users).contains("Bob")
```

### The `expect` API

Use `expect` to perform tests on objects by chaining together methods. Using `expect` allows Ward
to provide detailed, highly readable output when your tests fail. 

```python
from ward import expect, fixture

@fixture
def cities():
    return {"edinburgh": "scotland", "tokyo": "japan", "madrid": "spain"}

def test_capital_cities(cities):
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
from ward import expect
from unittest.mock import Mock

def test_mock_was_called():
    mock = Mock()
    mock(1, 2, x=3)
    expect(mock).called_once_with(1, 2, x=3)
```

### Checking for exceptions

The test below will pass, because a `ZeroDivisionError` is raised. If a `ZeroDivisionError` wasn't raised,
the test would fail.

```python
from ward import raises

def test_expecting_an_exception():
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


### Filtering tests by name

You can choose to limit which tests are collected and ran by Ward 
using the `--filter` option. Test names which contain the argument value 
as a substring will be run, and everything else will be ignored.

To run a test called `test_the_sky_is_blue`:

```text
ward --filter test_the_sky_is_blue
```

The match takes place on the fully qualified name, so you can run a single
module (e.g. `my_module`) using the following command:

```text
ward --filter my_module.
```

### Skipping a test

Use the `@skip` annotation to tell Ward not to execute a test.

```python
from ward import skip

@skip
def test_to_be_skipped():
    pass
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
    <td align="center"><a href="https://darrenburns.net"><img src="https://avatars0.githubusercontent.com/u/5740731?v=4" width="100px;" alt="Darren Burns"/><br /><sub><b>Darren Burns</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=darrenburns" title="Code">💻</a> <a href="https://github.com/darrenburns/ward/commits?author=darrenburns" title="Documentation">📖</a> <a href="#ideas-darrenburns" title="Ideas, Planning, & Feedback">🤔</a> <a href="#review-darrenburns" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/darrenburns/ward/issues?q=author%3Adarrenburns" title="Bug reports">🐛</a> <a href="#example-darrenburns" title="Examples">💡</a></td>
    <td align="center"><a href="https://github.com/khusrokarim"><img src="https://avatars0.githubusercontent.com/u/1615476?v=4" width="100px;" alt="khusrokarim"/><br /><sub><b>khusrokarim</b></sub></a><br /><a href="#ideas-khusrokarim" title="Ideas, Planning, & Feedback">🤔</a></td>
  </tr>
</table>

<!-- markdownlint-enable -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!