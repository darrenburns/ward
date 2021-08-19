# What is this directory?

This directory exists for testing purposes. It contains subdirectories that we can run Ward on.

Any tests found in these directories are explicitly excluded from the main Ward suite via the
`exclude` config option in `pyproject.toml`.

These directories may be used in the unit testing suite, or could be used as
part of the end-to-end testing process to ensure Ward runs as expected on unusual scenarios
(e.g. deeply nested directory structures, unusual import patterns, etc.)

It may contain multiple example test directories of different structures.
