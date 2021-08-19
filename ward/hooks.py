import importlib
from typing import Iterable, List, Optional

import pluggy
from rich.console import ConsoleRenderable

from ward.config import Config
from ward.models import ExitCode
from ward.testing import Test, TestResult

PROJECT_NAME = "ward"

spec = pluggy.HookspecMarker(PROJECT_NAME)
hook = pluggy.HookimplMarker(PROJECT_NAME)


def register_hooks_in_modules(
    plugin_manager: pluggy.PluginManager, module_names: Iterable[str]
):
    for module_name in module_names:
        _register_hooks_in_module(plugin_manager, module_name)


def _register_hooks_in_module(plugin_manager: pluggy.PluginManager, module_name: str):
    module = importlib.import_module(module_name)
    plugin_manager.register(module)


class SessionHooks:
    @spec
    def before_session(self, config: Config) -> Optional[ConsoleRenderable]:
        """
        Hook which is called immediately at the start of a test session (before tests are collected).

        You can implement this hook to run some setup code.

        This hook has no default implementation. If you implement it, you will not be
        overriding any existing functionality.

        Examples of how you could use this hook:

        * Printing some information to the terminal about your plugin.
        * Creating a file on disk which you'll write to in other hooks.

        If you return a
        `rich.console.ConsoleRenderable<https://rich.readthedocs.io/en/latest/protocol.html#console-render>`_
        from this function, it will be rendered to the terminal.
        """

    @spec
    def after_session(
        self,
        config: Config,
        test_results: List[TestResult],
        status_code: ExitCode,
    ) -> Optional[ConsoleRenderable]:
        """
        Hook that runs right before a test session ends (just before the result summary is printed to the terminal).

        This hook has no default implementation. If you implement it, you will not be
        overriding any existing functionality.

        Examples of how you could use this hook:

        * Writing additional information to the terminal after the test session finishes.
        * Writing a file (e.g. an HTML report) to disk containing the results from the test session.
        * Sending a file containing the results off somewhere for storage/processing.

        If you return a
        `rich.console.ConsoleRenderable <https://rich.readthedocs.io/en/latest/protocol.html#console-render>`_
        from this function, it will be rendered to the terminal.
        """

    @spec
    def preprocess_tests(self, config: Config, collected_tests: List[Test]):
        """
        Called before tests are filtered out by ``--search``, ``--tags``, etc, and before assertion rewriting.

        Allows you to transform or filter out tests (by modifying the ``collected_tests`` list in place).

        This hook has no default implementation. You can implement it without overriding existing functionality.

        Examples of how you could use this hook:

        * Filter out tests
        * Reorder tests
        * Generate statistics about tests pre-run
        * Attach some data to each test to use later
        """


plugins = pluggy.PluginManager(PROJECT_NAME)
plugins.add_hookspecs(SessionHooks)
plugins.load_setuptools_entrypoints(PROJECT_NAME)
