<img src="https://user-images.githubusercontent.com/5740731/119056107-085c6900-b9c2-11eb-9699-f54ef4945623.png" width="350px">

[![Codecov](https://codecov.io/gh/darrenburns/ward/branch/master/graph/badge.svg)](https://codecov.io/gh/darrenburns/ward)
[![Documentation Status](https://readthedocs.org/projects/ward/badge/?version=latest)](https://ward.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/ward.svg)](https://badge.fury.io/py/ward)

<hr>

_Ward_ is a Python testing framework with a focus on productivity and readability. It gives you the tools you need to write **well-documented** and **scalable** tests.

> [!IMPORTANT]  
> I am no longer actively maintaining this project.

<img alt="Ward typical test output example" src="https://user-images.githubusercontent.com/5740731/118399779-a795ff00-b656-11eb-8fca-4ceb03151f3e.png">

## Features

See the full set of features in the [**documentation**](https://ward.readthedocs.io).

**Descriptive test names:** describe what your tests do using strings, not function names.
```python
@test("simple addition")  # you can use markdown in these descriptions!
def _():
    assert 1 + 2 == 3  # you can use plain assert statements!
```

**Modular test dependencies:** manage test setup/teardown code using fixtures that rely on Python's import system, not
name matching.
```python
@fixture
def user():
    return User(name="darren")


@test("the user is called darren")
def _(u=user):
    assert u.name == "darren"
```

**Support for asyncio**: define your tests and fixtures with `async def` and call asynchronous code within them.

```python
@fixture
async def user():
    u = await create_user()
    return await u.login()


@test("the logged in user has a last session date")
async def _(user=user):
    last_session = await get_last_session_date(user.id)
    assert is_recent(last_session, get_last_session_date)
```

**Powerful test selection:** limit your test run not only by matching test names/descriptions, but also on the code
contained in the body of the test.
```
ward --search "Database.get_all_users"
```
Or use tag expressions for more powerful filtering.
```
ward --tags "(unit or integration) and not slow"
```

**Parameterised testing:** write a test once, and run it multiple times with different inputs by writing it in a loop.
```python
for lhs, rhs, res in [
    (1, 1, 2),
    (2, 3, 5),
]:

    @test("simple addition")
    def _(left=lhs, right=rhs, result=res):
        assert left + right == result
```

**Cross platform:** Tested on Mac OS, Linux, and Windows.

**Speedy:** Ward's suite of ~320 tests run in less than half a second on my machine.

**Zero config:** Sensible defaults mean running `ward` with no arguments is enough to get started. Can be configured using `pyproject.toml` or the command line if required.

**Extendable:** Ward has a plugin system built with pluggy, the same framework used by pytest.

**Colourful, human readable output:** quickly pinpoint and fix issues with detailed output for failing tests.

<img alt="Ward failing test output example" src="https://user-images.githubusercontent.com/5740731/120125898-5dfaf780-c1b2-11eb-9acd-b9cd0ff24110.png">

## Getting Started

Have a look at the [**documentation**](https://ward.readthedocs.io)!

## How to Contribute

Contributions are very welcome and encouraged!

See the [contributing guide](.github/CONTRIBUTING.md) for information on how you can take part in the development of Ward.
