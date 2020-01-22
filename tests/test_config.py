import tempfile
from pathlib import Path

from ward import test, fixture, expect
from ward.config import read_config_toml


@fixture
def temp_config_file():
    conf = """
[tool.ward]
path="test_path"

[tool.other]
ignore="me"
"""
    with tempfile.NamedTemporaryFile() as temp:
        temp.write(bytes(conf, encoding="utf-8"))
        temp.seek(0)
        yield temp


@test("read_config_toml reads 'path' from [tool.ward] section")
def _(tmp=temp_config_file):
    conf = read_config_toml(Path(tempfile.gettempdir()), tmp.name)
    expect(conf).equals({"path": "test_path"})
