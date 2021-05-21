Your First Tests
================

In this tutorial, we'll write two tests using Ward.
These tests aren't realistic, nor is the function we're testing. This page exists to give a tour of some of the main features
of Ward and their motivations.
We'll define reusable test data in a fixture, and pass that data into our tests.
Finally, we'll look at how we can cache that test data to improve performance.

Installing Ward
---------------

Ward is available on PyPI, so it can be installed using pip: ``pip install ward``.

When you run ``ward`` with no arguments, it will recursively look for tests starting from your current directory.

Ward will look for tests in any Python module with a name that starts with ``test_`` or ends with ``_test``.

We're going to write tests for a function called ``contains``:

.. code-block:: python

    def contains(list_of_items, target_item):
        ...

This function should return ``True`` if the ``target_item`` is contained within ``list_of_items``. Otherwise it should return ``False``.

Our first test
--------------

Tests in Ward are just Python functions decorated with ``@test(description: str)``.

Functions with this decorator can be named ``_``.
We'll tell readers what the test does using a plain English description rather than the function name.

Our test is contained within a file called ``test_contains.py``:

.. code-block:: python

    from contains import contains
    from ward import test


    @test("contains returns True when the item is in the list")
    def _():
        list_of_ints = list(range(100000))
        result = contains(list_of_ints, 5)
        assert result

In this file, we've defined a single test function called ``_``. It's been decorated with ``@test``, and has a helpful description.
We don't have to read the code inside the test to understand its purpose.

The description can be queried when running a subset of tests. You may decide to use your own conventions inside the description in order to make your tests highly queryable.

Now we can run ``ward`` in our terminal.

Ward will find and run the test, and confirm that the test PASSED with a message like the one below.

.. code-block:: text

    PASS test_contains:4: contains returns True when item is in list

Fixtures: Extracting common setup code
--------------------------------------

Lets add another test.

.. code-block:: python

    @test("contains returns False when item is not in list")
    def _():
        list_of_ints = list(range(100000))
        result = contains(list_of_ints, -1)
        assert not result

This test begins by instantiating the same list of 10 integers as the first test. This duplicated setup code can be extracted out into a fixture so that we don't have to repeat ourselves at the start of every test.

The ``@fixture`` decorator lets us define a fixture, which is a unit of test setup code. It can optionally contain some additional code to clean up any resources the it used (e.g. cleaning up a test database).

Lets define a fixture immediately above the tests we just wrote.

.. code-block:: python

    from ward import fixture


    @fixture
    def list_of_ints():
        return list(range(100000))

We can now rewrite our tests to make use of this fixture. Here's how we'd rewrite the second test.

.. code-block:: python

    @test("contains returns False when item is not in list")
    def _(l=list_of_ints):
        result = contains(l, -1)
        assert not result

By binding the name of the fixture as a default argument to the test, Ward will resolve it before the test runs, and inject it into the test.

By default, a fixture is executed immediately before being injected into a test. In the case of ``list_of_ints``, that could be problematic if lots of tests depend on it.
Do we really want to instantiate a list of 100000 integers before each of those tests? Probably not.

Improving performance with fixture scoping
------------------------------------------

To avoid this repeated expensive test setup, you can tell Ward what the scope of a fixture is. The scope of a fixture defines how long it should be cached for.

Ward supports 3 scopes: test (default), module, and global.

* A *test* scoped fixture will be evaluated at most once per test.
* A *module* scoped fixture will be evaluated at most once per test module.
* A *global* scoped fixture will be evaluated at most once per invocation of ``ward``.

If a fixture is never injected into a test or another fixture, it will never be evaluated.

We can safely say that we only need to generate our ``list_of_ints`` once, and we can reuse its value in every test that depends on it.
So lets give it a global scope:

.. code-block:: python

    from ward import fixture, Scope


    @fixture(scope=Scope.Global)  # or scope="global"
    def list_of_ints():
        return list(range(100000))

With this change, our fixture will now only be evaluated once, regardless of how many tests depend on it.
Careful management of fixture scope can drastically reduce the time and resources required to run a suite of tests.

As a general rule of thumb, if the value returned by a fixture is immutable, or we know that no test will mutate it, then we can make it global.

.. warning:: You should *never* mutate a global or module scoped fixture. Doing so breaks the isolated nature of tests, and introduces hidden dependencies between them.

Summary
-------

In this tutorial, you learned how to write your first tests with Ward. We covered how to write a test, inject a fixture into it, and cache the fixture for performance.
