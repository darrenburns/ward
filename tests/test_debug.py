import os
from types import SimpleNamespace
from unittest import mock
from unittest.mock import Mock

from ward import test, debug
from ward.debug import init_breakpointhooks, _breakpointhook


@test("init_breakpointhooks always patches pdb.set_trace")
def _():
    mock_pdb = Mock()
    init_breakpointhooks(pdb_module=mock_pdb, sys_module=Mock())
    assert mock_pdb.set_trace == _breakpointhook


@test("init_breakpointhooks sets sys.breakpointhook when it's supported")
def _():
    old_func = debug._breakpoint_supported
    debug._breakpoint_supported = lambda: True
    mock_sys = SimpleNamespace()
    init_breakpointhooks(pdb_module=Mock(), sys_module=mock_sys)
    debug._breakpoint_supported = old_func
    assert mock_sys.breakpointhook == _breakpointhook


@test("init_breakpointhooks doesnt set breakpointhook when it's unsupported")
def _():
    old_func = debug._breakpoint_supported
    debug._breakpoint_supported = lambda: False
    mock_sys = SimpleNamespace()
    init_breakpointhooks(pdb_module=Mock(), sys_module=mock_sys)
    debug._breakpoint_supported = old_func
    assert not hasattr(mock_sys, "breakpointhook")


@test("_breakpointhook returns None if PYTHONBREAKPOINT env var is '0'")
def _():
    with mock.patch.dict(os.environ, {"PYTHONBREAKPOINT": "0"}):
        assert _breakpointhook() is None


