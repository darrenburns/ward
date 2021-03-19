# Ward
![Build](https://github.com/darrenburns/ward/workflows/Build/badge.svg)
[![Codecov](https://codecov.io/gh/darrenburns/ward/branch/master/graph/badge.svg)](https://codecov.io/gh/darrenburns/ward)
[![PyPI version](https://badge.fury.io/py/ward.svg)](https://badge.fury.io/py/ward)
[![Gitter](https://badges.gitter.im/python-ward/community.svg)](https://gitter.im/python-ward/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge) <!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-14-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

See the full documentation and feature set [here](https://wardpy.com).

A modern Python test framework designed to help you find and fix flaws faster.

<img width="567" alt="image" src="https://user-images.githubusercontent.com/5740731/111796103-bfa00b00-88bf-11eb-91a5-63622b2426c1.png">

## Features

**Descriptive test names:** describe what your tests do using strings, not function names.
```python
@test("1 + 2 == 3")
def _():
    assert 1 + 2 == 3
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

**Parameterised testing:** write a test once, and call it multiple times with different inputs
```python
@test("truncate('{text}', num_chars={num_chars}) returns '{expected}'")
def _(
    text=s,
    num_chars=each(20, 11, 10, 5),
    expected=each(s, s, "hello w...", "he..."),
):
    result = truncate(text, num_chars)
    assert result == expected
```

**Cross platform:** Tested on Mac OS, Linux, and Windows.

**Zero config:** Sensible defaults mean running `ward` with no arguments is enough to get started. Can be configured using `pyproject.toml` or the command line if required.

**Colourful, human readable output:** quickly pinpoint and fix issues with detailed output for failing tests.

This project is currently in beta.

Planned features:

* Smart test execution order designed to surface failures faster (using various heuristics)
* Multi-process mode to improve performance
* Code coverage with `--coverage` flag
* Handling flaky tests with test-specific retries, timeouts
* Plugin system

Let me know if you'd like to help out with any of these features!

## Getting Started

[Take a look at the "Getting Started" tutorial.](https://wardpy.com/guide/tutorial)

## How to Contribute

Contributions are very welcome and encouraged!

See the [contributing guide](.github/CONTRIBUTING.md) for information on how you can take part in the development of Ward.

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://darrenburns.net"><img src="https://avatars0.githubusercontent.com/u/5740731?v=4" width="60px;" alt=""/><br /><sub><b>Darren Burns</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=darrenburns" title="Code">💻</a> <a href="https://github.com/darrenburns/ward/commits?author=darrenburns" title="Documentation">📖</a> <a href="#ideas-darrenburns" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/darrenburns/ward/pulls?q=is%3Apr+reviewed-by%3Adarrenburns" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/darrenburns/ward/issues?q=author%3Adarrenburns" title="Bug reports">🐛</a> <a href="#example-darrenburns" title="Examples">💡</a></td>
    <td align="center"><a href="https://github.com/khusrokarim"><img src="https://avatars0.githubusercontent.com/u/1615476?v=4" width="60px;" alt=""/><br /><sub><b>khusrokarim</b></sub></a><br /><a href="#ideas-khusrokarim" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/darrenburns/ward/commits?author=khusrokarim" title="Code">💻</a> <a href="https://github.com/darrenburns/ward/issues?q=author%3Akhusrokarim" title="Bug reports">🐛</a></td>
    <td align="center"><a href="https://github.com/AlecJ"><img src="https://avatars2.githubusercontent.com/u/5054790?v=4" width="60px;" alt=""/><br /><sub><b>Alec Jordan</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=AlecJ" title="Code">💻</a></td>
    <td align="center"><a href="https://www.indeliblebluepen.com"><img src="https://avatars2.githubusercontent.com/u/7471402?v=4" width="60px;" alt=""/><br /><sub><b>Jason C. McDonald</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=CodeMouse92" title="Code">💻</a> <a href="#ideas-CodeMouse92" title="Ideas, Planning, & Feedback">🤔</a></td>
    <td align="center"><a href="https://github.com/AndydeCleyre"><img src="https://avatars3.githubusercontent.com/u/1787385?v=4" width="60px;" alt=""/><br /><sub><b>Andy Kluger</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=AndydeCleyre" title="Code">💻</a> <a href="#ideas-AndydeCleyre" title="Ideas, Planning, & Feedback">🤔</a></td>
    <td align="center"><a href="https://forum.thebigmunch.me"><img src="https://avatars0.githubusercontent.com/u/118418?v=4" width="60px;" alt=""/><br /><sub><b>thebigmunch</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=thebigmunch" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/onlyanegg"><img src="https://avatars0.githubusercontent.com/u/7731128?v=4" width="60px;" alt=""/><br /><sub><b>Tyler Couto</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=onlyanegg" title="Code">💻</a></td>
  </tr>
  <tr>
    <td align="center"><a href="https://github.com/thilp"><img src="https://avatars2.githubusercontent.com/u/968838?v=4" width="60px;" alt=""/><br /><sub><b>Thibaut Le Page</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=thilp" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/DorianCzichotzki"><img src="https://avatars1.githubusercontent.com/u/10177001?v=4" width="60px;" alt=""/><br /><sub><b>Dorian Czichotzki</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=DorianCzichotzki" title="Code">💻</a> <a href="#ideas-DorianCzichotzki" title="Ideas, Planning, & Feedback">🤔</a></td>
    <td align="center"><a href="https://github.com/jayeshathila"><img src="https://avatars0.githubusercontent.com/u/1469191?v=4" width="60px;" alt=""/><br /><sub><b>jayesh hathila</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=jayeshathila" title="Code">💻</a></td>
    <td align="center"><a href="https://mandarvaze.bitbucket.io/"><img src="https://avatars1.githubusercontent.com/u/46438?v=4" width="60px;" alt=""/><br /><sub><b>Mandar Vaze</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=mandarvaze" title="Code">💻</a></td>
    <td align="center"><a href="https://www.jtk.dev"><img src="https://avatars2.githubusercontent.com/u/7133863?v=4" width="60px;" alt=""/><br /><sub><b>Josh Karpel</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=JoshKarpel" title="Code">💻</a></td>
    <td align="center"><a href="https://www.lutro.me"><img src="https://avatars0.githubusercontent.com/u/163093?v=4" width="60px;" alt=""/><br /><sub><b>Andreas Lutro</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=anlutro" title="Code">💻</a></td>
    <td align="center"><a href="https://hoefling.io"><img src="https://avatars1.githubusercontent.com/u/4455652?v=4" width="60px;" alt=""/><br /><sub><b>Oleg Höfling</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=hoefling" title="Code">💻</a></td>
  </tr>
</table>

<!-- markdownlint-enable -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
