import asyncio
import inspect
from contextlib import ExitStack, redirect_stderr, redirect_stdout, suppress
from dataclasses import dataclass
from functools import partial, wraps
from io import StringIO
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Generator, List, Optional, Union, cast

from ward.models import CollectionMetadata, Scope

__all__ = ["fixture", "using", "Fixture", "TeardownResult"]


@dataclass
class Fixture:
    """
    Represents a piece of data that will be used in a test.

    Attributes:
        fn: The Python function object corresponding to this fixture.
        gen: The generator, if applicable to this fixture.
        resolved_val: The value returned by calling the fixture function (fn).
    """

    fn: Callable
    gen: Union[Generator, AsyncGenerator, None] = None
    resolved_val: Any = None

    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        return self._id == other._id

    @property
    def _id(self):
        return self.__class__, self.name, self.path, self.line_number

    @property
    def key(self) -> str:
        """
        A unique key used to identify fixture in the fixture cache. A string of the form '{path}::{name}'
        """
        path = self.path
        name = self.name
        return f"{path}::{name}"

    @property
    def scope(self) -> Scope:
        return getattr(self.fn, "ward_meta").scope

    @property
    def name(self):
        """
        The name of the fixture function.
        """
        return self.fn.__name__

    @property
    def path(self):
        """
        The pathlib.Path of the module the fixture is defined in.
        """
        return self.fn.ward_meta.path

    @property
    def module_name(self):
        """
        The name of the module the fixture is defined in.
        """
        return self.fn.__module__

    @property
    def qualified_name(self) -> str:
        name = self.name or ""
        return f"{self.module_name}.{name}"

    @property
    def line_number(self) -> int:
        """
        The line number that the fixture is defined on.
        """
        return inspect.getsourcelines(self.fn)[1]

    @property
    def is_generator_fixture(self):
        """
        True if the fixture is a generator function (and thus may contain teardown code).
        """
        return inspect.isgeneratorfunction(inspect.unwrap(self.fn))

    @property
    def is_async_generator_fixture(self):
        """
        True if this fixture is an async generator.
        """
        return inspect.isasyncgenfunction(inspect.unwrap(self.fn))

    @property
    def is_coroutine_fixture(self):
        """
        True if the fixture is defined with 'async def'.
        """
        return inspect.iscoroutinefunction(inspect.unwrap(self.fn))

    def deps(self):
        """
        The dependencies of the fixture.
        """
        return inspect.signature(self.fn).parameters

    def parents(self) -> List["Fixture"]:
        """
        Return the parent fixtures of this fixture, as a list of Fixtures.
        """
        return [Fixture(par.default) for par in self.deps().values()]

    def teardown(self, capture_output: bool) -> "TeardownResult":
        """
        Tears down the fixture by calling `next` or `__anext__()`.
        """
        # Suppress because we can't know whether there's more code
        # to execute below the yield.
        teardown_result = TeardownResult(fixture=self)
        captured_stdout = StringIO()
        captured_stderr = StringIO()

        try:
            with ExitStack() as stack:
                stack.enter_context(suppress(StopIteration, StopAsyncIteration))
                if capture_output:
                    stack.enter_context(redirect_stdout(captured_stdout))
                    stack.enter_context(redirect_stderr(captured_stderr))

                if self.is_generator_fixture and self.gen:
                    next(cast(Generator, self.gen))
                elif self.is_async_generator_fixture and self.gen:
                    awaitable = cast(AsyncGenerator, self.gen).__anext__()
                    asyncio.run(awaitable)
        except Exception as e:
            # Note that with StopIterations being suppressed, we have an issue
            # that if a StopIteration occurs in fixture teardown code, it will
            # not be recorded as an error in the fixture.
            teardown_result.captured_exception = e

        captured_stdout.seek(0)
        captured_stderr.seek(0)
        teardown_result.sout = captured_stdout.read()
        teardown_result.serr = captured_stderr.read()
        captured_stdout.close()
        captured_stderr.close()

        return teardown_result


@dataclass
class TeardownResult:
    """
    Contains data associated with execution of fixture teardown code,
    for example, stdout and stderr that was captured by the framework
    during this process.
    """

    fixture: Fixture
    captured_exception: Optional[Exception] = None
    sout: str = ""
    serr: str = ""


def fixture(func=None, *, scope: Union[Scope, str] = Scope.Test):
    """
    Decorator which will cause the wrapped function to be collected and treated as a fixture.

    Args:
        func: The wrapped function which should yield or return some data required to execute a test.
        scope: The scope of a fixture determines how long it can be cached for (and therefore how frequently
            the fixture should be regenerated).
    """
    if not isinstance(scope, Scope):
        scope = Scope.from_str(scope)

    if func is None:
        return partial(fixture, scope=scope)

    # By setting is_fixture = True, the framework will know
    # that if this fixture is provided as a default arg, it
    # is responsible for resolving the value.
    path = Path(inspect.getfile(func)).absolute()
    if hasattr(func, "ward_meta"):
        func.ward_meta.is_fixture = True
        func.ward_meta.path = path
    else:
        func.ward_meta = CollectionMetadata(is_fixture=True, scope=scope, path=path)

    _DEFINED_FIXTURES.append(Fixture(func))

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def using(*using_args, **using_kwargs):
    """
    An alternative to the default param method of injecting fixtures into tests. Allows you to avoid using
    keyword arguments in your test definitions.
    """

    def decorator_using(func):
        signature = inspect.signature(func)
        bound_args = signature.bind_partial(*using_args, **using_kwargs)
        if hasattr(func, "ward_meta"):
            func.ward_meta.bound_args = bound_args
        else:
            func.ward_meta = CollectionMetadata(bound_args=bound_args)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator_using


_DEFINED_FIXTURES: List[Fixture] = []
