import importlib
import inspect
import io
import os
import warnings

import click
import sys

from ward.config import _breakpoint_supported
from ward.terminal import console

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

    modname, dot, funcname = hookname.rpartition(".")
    if dot == "":
        modname = "builtins"

    try:
        module = importlib.import_module(modname)
        if hookname == "pdb.set_trace":
            set_trace = module.Pdb(stdout=original_stdout, skip=["ward*"]).set_trace
            hook = set_trace
        else:
            hook = getattr(module, funcname)
    except:
        warnings.warn(
            f"Ignoring unimportable $PYTHONBREAKPOINT: {hookname}", RuntimeWarning
        )
        return None

    context = click.get_current_context()
    capture_enabled = context.params.get("capture_output")
    capture_active = isinstance(sys.stdout, io.StringIO)

    if capture_enabled and capture_active:
        sys.stdout = original_stdout
        console.print(f"Entering {modname} - output capturing disabled.", style="info")
        return hook(*args, **kwargs)
    return hook(*args, **kwargs)


__breakpointhook__ = _breakpointhook
