import importlib
import inspect
import io
import os
import sys
from typing import Any

import click

from ward._config import _breakpoint_supported
from ward._terminal import rich_console

original_stdout = sys.stdout


def init_breakpointhooks(pdb_module, sys_module) -> None:
    # breakpoint() is Python 3.7+
    if _breakpoint_supported():
        sys_module.breakpointhook = _breakpointhook
    pdb_module.set_trace = _breakpointhook


def _breakpointhook(*args, **kwargs):
    hookname = os.getenv("PYTHONBREAKPOINT")
    if hookname is None or len(hookname) == 0:
        hookname = "pdb.set_trace"
        kwargs.setdefault("frame", inspect.currentframe().f_back)
    elif hookname == "0":
        return None

    hook = _get_debugger_hook(hookname)
    context = click.get_current_context()
    capture_enabled = context.params.get("capture_output")
    capture_active = isinstance(sys.stdout, io.StringIO)

    # Stop an active Live.
    # It is the responsibility of the test executor
    # to re-enable the Live.
    live = rich_console._live
    if live is not None:
        live.refresh()
        live.stop()

    if capture_enabled and capture_active:
        sys.stdout = original_stdout
        rich_console.print(
            f"Entering debugger [bold]{hookname}[/] - output capturing disabled.",
            style="info",
        )

    return hook(*args, **kwargs)


def _get_debugger_hook(hookname: str):
    modname, dot, funcname = hookname.rpartition(".")
    if dot == "":
        modname = "builtins"
    module: Any = importlib.import_module(modname)
    if hookname == "pdb.set_trace":
        set_trace = module.Pdb(stdout=original_stdout, skip=["ward*"]).set_trace
        hook = set_trace
    else:
        hook = getattr(module, funcname)
    return hook


__breakpointhook__ = _breakpointhook
