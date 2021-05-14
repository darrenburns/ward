.. _extending_ward:

Extending Ward
##############

You can have Ward call custom Python code at various points during a test session. To do this, you must provide your
own implementation of a *hook* function, which Ward will call for you. The signature of the function must match the
signatures listed below, and the function must be decorated with ``@hook``.

You can write these hooks inside your test project, or inside a separate package. You can upload your package to PyPI in
order to share it with others.

If you implement the hooks inside your test project, you'll need to register them in your ``pyproject.toml`` config file, so
that Ward knows where to find your custom implementations:

.. code-block:: toml

    hook_module = ["module.containing.hooks"]

You can also tell Ward where your hook implementations via the equivalent command line option: ``--hook-module=module.containing.hooks``.

You can specify multiple ``hook_module`` and they will all be loaded. If the same hook is implemented in multiple modules, they will all be called (unless configured otherwise).

If you write them in a separate Python package (i.e., a plugin), then they can be registered automatically, assuming the ``setup.py`` of the package
is configured to use the ``ward`` entry point.

What hooks are available?
*************************

Run code *before* the test run with ``before_session``
======================================================

.. automethod:: ward.hooks::SessionHooks.before_session

Example: printing information to the terminal
---------------------------------------------

.. image:: ../_static/plugins_printing_before.png
    :align: center
    :alt: Example of implementing before_session hook

Here's how you could implement a hook in order to achieve the outcome shown above.

.. code-block:: python

    from rich.console import RenderResult, Console, ConsoleOptions, ConsoleRenderable
    from ward.config import Config
    from ward.hooks import hook

    @hook
    def before_session(config: Config) -> Optional[ConsoleRenderable]:
        return WillPrintBefore()

    class WillPrintBefore:
        def __rich_console__(
            self, console: Console, console_options: ConsoleOptions
        ) -> RenderResult:
            yield Panel(Text("Hello from 'before session'!", style="info"))


Run code *after* the test run with ``after_session``
====================================================

.. automethod:: ward.hooks::SessionHooks.after_session

Example: printing information about the session to the terminal
---------------------------------------------------------------

.. image:: ../_static/plugins_printing_after_session.png
    :align: center
    :alt: Example of implementing after_session hook

Here's how you could implement a hook in order to achieve the outcome shown above.

.. code-block:: python

    from typing import Optional, List

    from rich.console import RenderResult, Console, ConsoleOptions, ConsoleRenderable
    from rich.panel import Panel
    from rich.text import Text
    from ward.config import Config
    from ward.hooks import hook
    from ward.testing import TestResult

    @hook
    def after_session(config: Config, results: List[TestResult]) -> Optional[ConsoleRenderable]:
        return SummaryPanel(test_results)

    class SummaryPanel:
        def __init__(self, results: List[TestResult]):
            self.results = results

        @property
        def time_taken(self):
            return sum(r.test.timer.duration for r in self.results)

        def __rich_console__(
            self, console: Console, console_options: ConsoleOptions
        ) -> RenderResult:
            yield Panel(
                Text(f"Hello from `after_session`! We ran {len(self.results)} tests!")
            )



Packaging your code into a plugin
*********************************

A *plugin* is a collection of hook implementations that come together to provide some functionality which can be shared with others.

If you've wrote implementations for one or more of the hooks provided by Ward, you can share those implementations
with others by creating a plugin and uploading it to PyPI.

Others can then install your plugin using a tool like ``pip`` or ``poetry``.

After they install your plugin, the hooks within will be registered automatically (no need to update any config).


