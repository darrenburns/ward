# Contributing

Contributions to Ward are encouraged and very welcome!

Contributions can come in many forms: documentation enhancements, features, bug fixes, creating issues, and participating in the community.

If you're interested in helping out, you might find some inspiration in [Issues](https://github.com/darrenburns/ward/issues). If you have an idea, but don't see it there, don't hesitate to open a new issue.

Before submitting a pull request, please make sure the enhancement or bugfix you've made has been discussed.

This will ensure no work is duplicated, and that a general approach has been agreed.

Please also take time to review the [Code of Conduct](https://github.com/darrenburns/ward/blob/master/.github/CODE_OF_CONDUCT.md). Anyone who violates the code of conduct may be barred from contributing.

## Local development setup

To get started with developing Ward, you'll need to [install Poetry](https://python-poetry.org/docs/#installation).
Then run `make setup` from the repository root to create a virtual environment for Ward's development dependencies and install the [pre-commit hooks](https://pre-commit.com/).
Any development commands you need from this point on can be also be found in the Makefile.
For example,
`make test` to run the tests,
`make format` to format your code,
`make prep` to do both of those things (run this before creating a PR).


## Pull request guidelines

* Let us know before you start working on something! Someone else may already have started working on the same thing.
* Prepare your code for review with `make prep` (this will run formatters and linters, and then run the test suite).
* Ensure `README.md` is updated if necessary.
* Tests written cover new code, and running `make test` results in a pass.

If something is missing from this guide (it probably is), please let me know by creating an issue or a pull request.
