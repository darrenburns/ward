import pluggy
from typing import Iterable

from ward.config import Config
from ward.testing import TestResult

PROJECT_NAME = "ward"

spec = pluggy.HookspecMarker(PROJECT_NAME)
hook = pluggy.HookimplMarker(PROJECT_NAME)


class SessionHooks:
    """
    The highest level of hooks offered by Ward, allowing you to run code before and
    after a test session. These hooks are not intended for outputting to the
    terminal. You can implement these hooks to call and API before/after a test session,
    write information about the results to a file, and more.
    """

    @spec
    def before_session(self, config: Config) -> None:
        """
        Hook which is called immediately at the start of a test session.
        """

    @spec
    def after_session(self, config: Config, test_results: Iterable[TestResult]) -> None:
        """
        Hook that runs right before a test session ends.
        """


class DefaultSessionHooks:
    @hook
    def before_session(self, config: Config) -> None:
        pass

    @hook
    def after_session(self, config: Config, test_results: Iterable[TestResult]) -> None:
        pass


plugins = pluggy.PluginManager(PROJECT_NAME)
plugins.add_hookspecs(SessionHooks)
plugins.load_setuptools_entrypoints(PROJECT_NAME)

plugins.register(DefaultSessionHooks())
