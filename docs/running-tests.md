## Test selection 

### Search and run matching tests with `--search`

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

**Run a test called `test_the_sky_is_blue`:**

```text
ward --search test_the_sky_is_blue
```

**Run a test described as `"my_function should return False"`:**

```text
ward --search "my_function should return False"
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

### Specific test selection

Sometimes you want to be very specific when declaring which tests to run.

Ward will provide an option to query tests on name and description using substring
or regular expression matching.

(TODO)

### Running tests in a directory

You can run tests in a specific directory using the `--path` option.
For example, to run all tests inside a directory called `tests`:

```text
ward --path tests
```

To run tests in the current directory, you can just type `ward`, which
is functionally equivalent to `ward --path .`

## Skipping a test

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

## Cancelling a run after a specific number of failures

If you wish for Ward to cancel a run immediately after a specific number of failing tests,
you can use the `--fail-limit` option. To have a run end immediately after 5 tests fail:

```text
ward --fail-limit 5
```
