# Ward
![](https://github.com/darrenburns/ward/workflows/Ward%20CI/badge.svg)
[![PyPI version](https://badge.fury.io/py/ward.svg)](https://badge.fury.io/py/ward) <!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->[![All Contributors](https://img.shields.io/badge/all_contributors-5-orange.svg?style=flat-square)](#contributors-)<!-- ALL-CONTRIBUTORS-BADGE:END -->

See the full documentation and feature set [here](https://wardpy.com).

A modern Python test framework designed to help you find and fix flaws faster.

## Features

**Descriptive test names:** describe what your tests do using strings, not function names.
```python
@test("1 + 2 gives 3")
def _():
    expect(1 + 2).equals(3)
```

**Modular test dependencies:** manage test setup/teardown code using fixtures that rely on Python's import system, not
name matching.
```python
@fixture
def user():
    return User(name="darren")
    
@test("the user is called darren")
def _(u=user):
    expect(u.name).equals("darren")
```

**Fast, minimal overhead:** roughly half the test run overhead of pytest. 

**Powerful test selection:** limit your test run not only by matching test names/descriptions, but also on the code 
contained in the body of the test.
```
ward --search "Database.get_all_users"
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
    expect(result).equals(expected)
```

**Expect API:** A simple but powerful assertion API inspired by [Jest](https://jestjs.io).

**Cross platform:** Tested on Mac OS, Linux, and Windows.

**Zero config:** Sensible defaults mean running `ward` with no arguments is enough to get started.

**Colourful, human readable output:** quickly pinpoint and fix issues with detailed output for failing tests.
![screenshot](https://raw.githubusercontent.com/darrenburns/ward/master/screenshot.png)

This project is currently in beta.

Planned features:

* Smart test execution order designed to surface failures faster (using various heuristics)
* Multi-process mode to improve performance
* Highly configurable output modes
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
    <td align="center"><a href="https://darrenburns.net"><img src="https://avatars0.githubusercontent.com/u/5740731?v=4" width="60px;" alt="Darren Burns"/><br /><sub><b>Darren Burns</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=darrenburns" title="Code">💻</a> <a href="https://github.com/darrenburns/ward/commits?author=darrenburns" title="Documentation">📖</a> <a href="#ideas-darrenburns" title="Ideas, Planning, & Feedback">🤔</a> <a href="#review-darrenburns" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/darrenburns/ward/issues?q=author%3Adarrenburns" title="Bug reports">🐛</a> <a href="#example-darrenburns" title="Examples">💡</a></td>
    <td align="center"><a href="https://github.com/khusrokarim"><img src="https://avatars0.githubusercontent.com/u/1615476?v=4" width="60px;" alt="khusrokarim"/><br /><sub><b>khusrokarim</b></sub></a><br /><a href="#ideas-khusrokarim" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/darrenburns/ward/commits?author=khusrokarim" title="Code">💻</a> <a href="https://github.com/darrenburns/ward/issues?q=author%3Akhusrokarim" title="Bug reports">🐛</a></td>
    <td align="center"><a href="https://github.com/AlecJ"><img src="https://avatars2.githubusercontent.com/u/5054790?v=4" width="60px;" alt="Alec Jordan"/><br /><sub><b>Alec Jordan</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=AlecJ" title="Code">💻</a></td>
    <td align="center"><a href="https://www.indeliblebluepen.com"><img src="https://avatars2.githubusercontent.com/u/7471402?v=4" width="60px;" alt="Jason C. McDonald"/><br /><sub><b>Jason C. McDonald</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=CodeMouse92" title="Code">💻</a> <a href="#ideas-CodeMouse92" title="Ideas, Planning, & Feedback">🤔</a></td>
    <td align="center"><a href="https://github.com/AndydeCleyre"><img src="https://avatars3.githubusercontent.com/u/1787385?v=4" width="60px;" alt="Andy Kluger"/><br /><sub><b>Andy Kluger</b></sub></a><br /><a href="https://github.com/darrenburns/ward/commits?author=AndydeCleyre" title="Code">💻</a> <a href="#ideas-AndydeCleyre" title="Ideas, Planning, & Feedback">🤔</a></td>
  </tr>
</table>

<!-- markdownlint-enable -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
