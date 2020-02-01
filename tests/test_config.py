import tempfile
from pathlib import Path

import click

from ward import test, fixture, raises, each
from ward.config import read_config_toml, as_list, apply_multi_defaults


def temp_conf(conf: str) -> tempfile._TemporaryFileWrapper:
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(bytes(conf, encoding="utf-8"))
        temp.seek(0)
        yield temp


@fixture
def temp_config_file():
    conf = """
[tool.ward]
path="test_path"

[tool.other]
ignore="me"
"""
    yield from temp_conf(conf)


@fixture
def temp_config_missing():
    conf = """
[tool.other]
hello="world"
"""
    yield from temp_conf(conf)


@fixture
def temp_config_invalid():
    conf = """
[tool.ward
path="section header is invalid"    
"""
    yield from temp_conf(conf)


@fixture
def temp_config_file_hyphens():
    conf = """
[tool.ward]
--some-key="some-value"
"""
    yield from temp_conf(conf)


@test("read_config_toml reads from only [tool.ward] section")
def _(tmp=temp_config_file):
    conf = read_config_toml(Path(tempfile.gettempdir()), tmp.name)
    assert conf == {"path": "test_path"}


@test("read_config_toml returns {} if config file doesnt exist")
def _():
    conf = read_config_toml(Path(tempfile.gettempdir()), "doesnt_exist.toml")
    assert conf == {}


@test("read_config_toml returns {} when [tool.ward] not present")
def _(tmp=temp_config_missing):
    conf = read_config_toml(Path(tempfile.gettempdir()), tmp.name)
    assert conf == {}


@test(
    "read_config_toml converts options to click argument names (converts/removes hyphens)"
)
def _(tmp=temp_config_file_hyphens):
    conf = read_config_toml(Path(tempfile.gettempdir()), tmp.name)
    assert conf == {"some_key": "some-value"}


@test("read_config_toml raises click.FileError if config file syntax invalid")
def _(tmp=temp_config_invalid):
    with raises(click.FileError):
        read_config_toml(Path(tempfile.gettempdir()), tmp.name)


@test("as_list({arg}) returns {rv}")
def _(arg=each("x", 1, True, ["a", "b"]), rv=each(["x"], [1], [True], ["a", "b"])):
    assert as_list(arg) == rv


@test("apply_multi_defaults returns {} when path in cli args and file")
def _():
    file_config = {"path": ["a", "b", "c"]}
    cli_config = {"path": ["a"]}
    assert apply_multi_defaults(file_config, cli_config) == {}


@test("apply_multi_defaults returns paths from file when path if no cli arg")
def _():
    file_config = {"path": ["a"]}
    cli_config = {"another_multi_option": "abc"}
    assert apply_multi_defaults(file_config, cli_config) == file_config


@test("apply_multi_defaults converts scalar multi-options to lists")
def _():
    file_config = {"path": "a"}
    cli_config = {"another": ["a"]}
    assert apply_multi_defaults(file_config, cli_config) == {"path": ["a"]}


@test("apply_multi_defaults prioritises cli {opt} over file defaults")
def _(opt=each("exclude")):
    file_config = {opt: ["a", "b", "c"]}
    cli_config = {opt: ["a"]}
    assert apply_multi_defaults(file_config, cli_config) == {"path": ["."]}
