import tempfile
from pathlib import Path

import click

from ward import test, fixture, expect, raises
from ward.config import read_config_toml


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
    expect(conf).equals({"path": "test_path"})


@test("read_config_toml returns {} if config file doesnt exist")
def _():
    conf = read_config_toml(Path(tempfile.gettempdir()), "doesnt_exist.toml")
    expect(conf).equals({})


@test("read_config_toml returns {} when [tool.ward] not present")
def _(tmp=temp_config_missing):
    conf = read_config_toml(Path(tempfile.gettempdir()), tmp.name)
    expect(conf).equals({})


@test("read_config_toml converts options to click argument names (converts/removes hyphens)")
def _(tmp=temp_config_file_hyphens):
    conf = read_config_toml(Path(tempfile.gettempdir()), tmp.name)
    expect(conf).equals({"some_key": "some-value"})


@test("read_config_toml raises click.FileError if config file syntax invalid")
def _(tmp=temp_config_invalid):
    with raises(click.FileError):
        read_config_toml(Path(tempfile.gettempdir()), tmp.name)
