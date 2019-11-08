# Ward
![](https://github.com/darrenburns/ward/workflows/Ward%20CI/badge.svg)
[![PyPI version](https://badge.fury.io/py/ward.svg)](https://badge.fury.io/py/ward) <!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->[![All Contributors](https://img.shields.io/badge/all_contributors-2-orange.svg?style=flat-square)](#contributors-)<!-- ALL-CONTRIBUTORS-BADGE:END -->

See the full documentation and feature set [here](https://wardpy.com).

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

*You've just wrote your first test with Ward, congrats!*

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
  </tr>
</table>

<!-- markdownlint-enable -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!