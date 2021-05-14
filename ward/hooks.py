import importlib
from typing import Iterable, Optional, List

import pluggy
from rich.console import ConsoleRenderable

from ward.config import Config
from ward.testing import TestResult

PROJECT_NAME = "ward"

spec = pluggy.HookspecMarker(PROJECT_NAME)
hook = pluggy.HookimplMarker(PROJECT_NAME)


def register_hooks_in_modules(module_names: Iterable[str]):
    for module_name in module_names:
        _register_hooks_in_module(module_name)


def _register_hooks_in_module(module_name: str):
    module = importlib.import_module(module_name)
    plugins.register(module)


class SessionHooks:
    """
    The highest level of hooks offered by Ward, allowing you to run code before and
    after a test session, or to create new command line options. You can implement these hooks to call and API before/after a test session,
    write information about the results to a file, and more.
    """

    @spec
    def before_session(self, config: Config) -> Optional[ConsoleRenderable]:
        """
        Hook which is called immediately at the start of a test session. You can implement this hook to run some setup code.

        This hook has no default implementation. If you implement it, you will not be overriding any existing functionality.

        Examples of how you could use this hook:

        * Printing some information to the terminal about your plugin.
        * Creating a file on disk which you'll write to in other hooks.

        If you return a `rich.console.ConsoleRenderable <https://rich.readthedocs.io/en/latest/protocol.html#console-render>`_
        from this function, it will be rendered to the terminal.
        """

    @spec
    def after_session(
        self, config: Config, test_results: List[TestResult]
    ) -> Optional[ConsoleRenderable]:
        """
        Hook that runs right before a test session ends (just before the result summary is printed to the terminal).

        This hook has no default implementation. If you implement it, you will not be overriding any existing functionality.

        Examples of how you could use this hook:

        * Writing additional information to the terminal after the test session finishes.
        * Writing a file (e.g. an HTML report) to disk containing the results from the test session.
        * Sending a file containing the results off somewhere for storage/processing.

        If you return a `rich.console.ConsoleRenderable <https://rich.readthedocs.io/en/latest/protocol.html#console-render>`_
        from this function, it will be rendered to the terminal.
        """


plugins = pluggy.PluginManager(PROJECT_NAME)
plugins.add_hookspecs(SessionHooks)
plugins.load_setuptools_entrypoints(PROJECT_NAME)
