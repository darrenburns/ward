import tempfile

from ward import test, fixture, Scope
from ward.config import read_config_toml


@fixture(scope=Scope.Module)
def temp_config_file():
    with tempfile.NamedTemporaryFile("r+b") as temp:
        yield temp


@test("read_config_toml reads from toml file [tool.ward] section")
def _(tmp=temp_config_file):
    print(tmp)
    # conf = read_config_toml(tempfile.gettempdir(), )
