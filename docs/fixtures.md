## Dependency injection with fixtures

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

Fixtures can be injected into each other, using the same syntax.

The fixture will be executed exactly once each time a test depends on it. 

More specifically, if a fixture F is required by multiple other fixtures that are all injected into a single
test, then F will only be resolved once.

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

The code below the `yield` statement in a fixture will be executed after the test that depends on it completes,
regardless of the result of the test. 