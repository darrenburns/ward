import tempfile
import types
from pathlib import Path
from typing import IO, Generator
from unittest import mock

import click

from tests.test_util import fake_project_empty, fake_project_pyproject
from ward import each, fixture, raises, test
from ward._config import (
    apply_multi_defaults,
    as_list,
    read_config_toml,
    set_defaults_from_config,
    validate_config_toml,
)


def temp_conf(conf: str) -> Generator[IO[bytes], None, None]:
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


@fixture
def temp_config_plugins():
    conf = """
[tool.ward]
built_in_config="some-value"

[tool.ward.plugins.apples]
num_apples = 3

[tool.ward.plugins.bananas]
num_bananas = 4
"""
    yield from temp_conf(conf)


@test("read_config_toml reads from only [tool.ward] section")
def _(tmp=temp_config_file):
    conf = read_config_toml(Path(tempfile.gettempdir()), tmp.name)
    assert "path" in conf
    assert conf["path"] == "test_path"


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
    assert "some_key" in conf
    assert conf["some_key"] == "some-value"


@test("read_config_toml reads plugin conf from [tool.ward.plugins.*]")
def _(tmp=temp_config_plugins):
    conf = read_config_toml(Path(tempfile.gettempdir()), tmp.name)
    assert conf == {
        "built_in_config": "some-value",
        "plugins": {
            "apples": {"num_apples": 3},
            "bananas": {"num_bananas": 4},
        },
    }


@test("read_config_toml raises click.FileError if config file syntax invalid")
def _(tmp=temp_config_invalid):
    with raises(click.FileError):
        read_config_toml(Path(tempfile.gettempdir()), tmp.name)


@test("validate_config_toml raises click.ClickException if conf key is invalid")
def _():
    invalid_key = "orderr"
    with raises(click.ClickException) as exc_info:
        validate_config_toml({invalid_key: "the key here is invalid"})
    assert invalid_key in str(exc_info.raised)


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


@test("set_defaults_from_config sets config defaults map correctly")
def _(project_root: Path = fake_project_pyproject):
    """
    This test checks the situation where we're currently
    present in a child directory of the project root.
    The paths in the default map should be configured to be
    relative to the project root, and NOT from the current
    working directory.
    """
    fake_context = types.SimpleNamespace(
        params={"path": (str(project_root),)},
        default_map={},
    )
    with mock.patch.object(Path, "cwd", return_value=project_root / "a" / "d"):
        assert set_defaults_from_config(fake_context, None, None) == fake_context.default_map  # type: ignore[arg-type]

    assert fake_context.default_map == {
        "exclude": (str(project_root / "a" / "b"),),
        "path": (str(project_root / "a"), str(project_root / "x" / "y")),
        "order": "hello world",
    }
    assert fake_context.params["config_path"] == project_root / "pyproject.toml"


@test(
    "set_defaults_from_config returns {} if project_root does not contain pyproject.toml"
)
def _(project_root: Path = fake_project_empty):
    """
    This test checks the situation where we're currently
    present in directory that has no pyproject.toml present
    """
    fake_context = types.SimpleNamespace(
        params={"path": (str(project_root),)},
        default_map={},
    )
    assert set_defaults_from_config(fake_context, None, None) == {}  # type: ignore[arg-type]

    assert fake_context.params["project_root"] is None
    assert fake_context.params["config_path"] is None
