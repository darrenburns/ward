import inspect
import os
from pdb import Pdb
from types import SimpleNamespace
from unittest import mock
from unittest.mock import Mock

from ward import _debug, test
from ward._debug import (
    _breakpointhook,
    _get_debugger_hook,
    importlib,
    init_breakpointhooks,
)


@test("init_breakpointhooks always patches pdb.set_trace")
def _():
    mock_pdb = Mock()
    init_breakpointhooks(pdb_module=mock_pdb, sys_module=Mock())
    assert mock_pdb.set_trace == _breakpointhook


@test("init_breakpointhooks sets sys.breakpointhook when it's supported")
def _():
    old_func = _debug._breakpoint_supported
    _debug._breakpoint_supported = lambda: True
    mock_sys = SimpleNamespace()
    init_breakpointhooks(pdb_module=Mock(), sys_module=mock_sys)
    _debug._breakpoint_supported = old_func
    assert mock_sys.breakpointhook == _breakpointhook


@test("init_breakpointhooks doesnt set breakpointhook when it's unsupported")
def _():
    old_func = _debug._breakpoint_supported
    _debug._breakpoint_supported = lambda: False
    mock_sys = SimpleNamespace()
    init_breakpointhooks(pdb_module=Mock(), sys_module=mock_sys)
    _debug._breakpoint_supported = old_func
    assert not hasattr(mock_sys, "breakpointhook")


@test("_breakpointhook returns None if PYTHONBREAKPOINT env var is '0'")
def _():
    with mock.patch.dict(os.environ, {"PYTHONBREAKPOINT": "0"}):
        assert _breakpointhook() is None


@test("_get_debugger_hook returns Pdb.set_trace if hookname is 'pdb.set_trace'")
def _():
    assert inspect.getsource(_get_debugger_hook("pdb.set_trace")) == inspect.getsource(
        Pdb().set_trace
    )


@test("_get_debugger_hook returns function from builtins if hookname contains no dot")
def _():
    def fake_hook():
        return 1

    fake_builtins = SimpleNamespace(my_function=fake_hook)
    with mock.patch.object(
        importlib, "import_module", return_value=fake_builtins, autospec=True
    ) as im:
        hook = _get_debugger_hook("my_function")

        im.assert_called_once_with("builtins")
        assert hook == fake_hook
