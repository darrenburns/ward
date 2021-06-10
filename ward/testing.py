import asyncio
import collections
import functools
import inspect
import traceback
from bdb import BdbQuit
from contextlib import ExitStack, closing, redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from enum import Enum, auto
from io import StringIO
from pathlib import Path
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Union,
)

from ward._errors import FixtureError, ParameterisationError
from ward._fixtures import FixtureCache, ScopeKey, is_fixture
from ward._testing import (
    COLLECTED_TESTS,
    Each,
    _FormatDict,
    _generate_id,
    _Timer,
    is_test_module_name,
)
from ward._utilities import get_absolute_path
from ward.fixtures import Fixture
from ward.models import CollectionMetadata, Marker, Scope, SkipMarker, XfailMarker

__all__ = [
    "test",
    "skip",
    "xfail",
    "each",
    "Test",
    "TestOutcome",
    "TestResult",
    "ParamMeta",
]


@dataclass
class ParamMeta:
    instance_index: int = 0
    group_size: int = 1


def each(*args):
    """
    Used to parameterise tests.

    This will likely be deprecated before Ward 1.0.

    See documentation for examples.
    """
    return Each(args)


def skip(
    func_or_reason: Union[str, Callable] = None,
    *,
    reason: str = None,
    when: Union[bool, Callable] = True,
):
    """
    Decorator which can be used to optionally skip tests.

    Args:
        func_or_reason (object): The wrapped test function to skip.
        reason: The reason the test was skipped. May appear in output.
        when: Predicate function. Will be called immediately before the test is executed.
            If it evaluates to True, the test will be skipped. Otherwise the test will run as normal.
    """
    if func_or_reason is None:
        return functools.partial(skip, reason=reason, when=when)

    if isinstance(func_or_reason, str):
        return functools.partial(skip, reason=func_or_reason, when=when)

    func = func_or_reason
    marker = SkipMarker(reason=reason, when=when)
    if hasattr(func, "ward_meta"):
        func.ward_meta.marker = marker
    else:
        func.ward_meta = CollectionMetadata(marker=marker)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def xfail(
    func_or_reason: Union[str, Callable] = None,
    *,
    reason: str = None,
    when: Union[bool, Callable] = True,
):
    """
    Decorator that can be used to mark a test as "expected to fail".

    Args:
        func_or_reason: The wrapped test function to mark as an expected failure.
        reason: The reason we expect the test to fail. May appear in output.
        when: Predicate function. Will be called immediately before the test is executed.
            If it evaluates to True, the test will be marked as an expected failure.
            Otherwise the test will run as normal.
    """
    if func_or_reason is None:
        return functools.partial(xfail, reason=reason, when=when)

    if isinstance(func_or_reason, str):
        return functools.partial(xfail, reason=func_or_reason, when=when)

    func = func_or_reason
    marker = XfailMarker(reason=reason, when=when)
    if hasattr(func, "ward_meta"):
        func.ward_meta.marker = marker
    else:
        func.ward_meta = CollectionMetadata(marker=marker)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@dataclass
class Test:
    """
    Representation of a test case.

    Attributes:
        fn: The Python function object that contains the test code.
        module_name: The name of the module the test is defined in.
        id: A unique UUID4 used to identify the test.
        marker: Attached by the skip and xfail decorators.
        description: The description of the test. A format string that can contain basic Markdown syntax.
        param_meta: If this is a parameterised test, contains info about the parameterisation.
        capture_output: If True, output will be captured for this test.
        sout: Buffer that fills with captured stdout as the test executes.
        serr: Buffer that fills with captured stderr as the test executes.
        ward_meta: Metadata that was attached to the raw functions collected by Ward's decorators.
        timer: Timing information about the test.
        tags: List of tags associated with the test.
    """

    fn: Callable
    module_name: str
    id: str = field(default_factory=_generate_id)
    marker: Optional[Marker] = None
    description: str = ""
    param_meta: ParamMeta = field(default_factory=ParamMeta)
    capture_output: bool = True
    sout: StringIO = field(default_factory=StringIO)
    serr: StringIO = field(default_factory=StringIO)
    ward_meta: CollectionMetadata = field(default_factory=CollectionMetadata)
    timer: Optional["_Timer"] = None
    tags: List[str] = field(default_factory=list)

    def __hash__(self):
        return hash((self.__class__, self.id))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    # FIXME:fix linter C901
    def run(self, cache: FixtureCache, dry_run=False) -> "TestResult":  # noqa: C901
        with ExitStack() as stack:
            self.timer = stack.enter_context(_Timer())
            if self.capture_output:
                stack.enter_context(redirect_stdout(self.sout))
                stack.enter_context(redirect_stderr(self.serr))

            if dry_run:
                with closing(self.sout), closing(self.serr):
                    result = TestResult(self, TestOutcome.DRYRUN)
                return result

            if isinstance(self.marker, SkipMarker) and self.marker.active:
                with closing(self.sout), closing(self.serr):
                    result = TestResult(self, TestOutcome.SKIP)
                return result

            try:
                resolved_args = self.resolver.resolve_args(cache)
                self.format_description(resolved_args)
                if self.is_async_test:
                    coro = self.fn(**resolved_args)
                    asyncio.get_event_loop().run_until_complete(coro)
                else:
                    self.fn(**resolved_args)
            except FixtureError as e:
                outcome = TestOutcome.FAIL
                error: Optional[Exception] = e
            except BdbQuit:
                # We don't want to treat the user quitting the debugger
                # as an exception, so we'll ignore BdbQuit. This will
                # also prevent a large pdb-internal stack trace flooding
                # the terminal.
                pass
            except (Exception, SystemExit) as e:
                error = e
                if isinstance(self.marker, XfailMarker) and self.marker.active:
                    outcome = TestOutcome.XFAIL
                else:
                    outcome = TestOutcome.FAIL
            else:
                error = None
                if isinstance(self.marker, XfailMarker) and self.marker.active:
                    outcome = TestOutcome.XPASS
                else:
                    outcome = TestOutcome.PASS

        with closing(self.sout), closing(self.serr):
            if outcome in (TestOutcome.PASS, TestOutcome.SKIP):
                result = TestResult(self, outcome)
            else:
                if isinstance(error, AssertionError):
                    error.error_line = traceback.extract_tb(
                        error.__traceback__, limit=-1
                    )[0].lineno
                result = TestResult(
                    self,
                    outcome,
                    error,
                    captured_stdout=self.sout.getvalue(),
                    captured_stderr=self.serr.getvalue(),
                )

        return result

    def fail_with_error(self, error: Exception) -> "TestResult":
        return TestResult(
            self, outcome=TestOutcome.FAIL, error=error, message=str(error)
        )

    @property
    def name(self) -> str:
        """The name of the Python function representing the test."""
        return self.fn.__name__

    @property
    def path(self) -> Path:
        """The pathlib.Path to the test module."""
        return self.fn.ward_meta.path

    @property
    def qualified_name(self) -> str:
        """{module_name}.{test_function_name}"""
        name = self.name or ""
        return f"{self.module_name}.{name}"

    @property
    def is_async_test(self) -> bool:
        """True if the test is defined with 'async def'."""
        return inspect.iscoroutinefunction(inspect.unwrap(self.fn))

    @property
    def line_number(self) -> int:
        """
        The line number the test is defined on. Corresponds to the line the first decorator wrapping the
            test appears on.
        """
        return inspect.getsourcelines(self.fn)[1]

    @property
    def has_deps(self) -> bool:
        return len(self.deps()) > 0

    @property
    def is_parameterised(self) -> bool:
        """
        `True` if a test is parameterised, `False` otherwise.
            A test is considered parameterised if any of its default arguments
            have a value that is an instance of `Each`.
        """
        default_args = self.resolver.get_default_args()
        return any(isinstance(arg, Each) for arg in default_args.values())

    @property
    def resolver(self):
        return TestArgumentResolver(self, self.param_meta.instance_index)

    def scope_key_from(self, scope: Scope) -> ScopeKey:
        if scope == Scope.Test:
            return self.id
        elif scope == Scope.Module:
            return self.path
        else:
            return Scope.Global

    def get_parameterised_instances(self) -> List["Test"]:
        """
        If the test is parameterised, return a list of `Test` objects representing
        each test generated as a result of the parameterisation.
        If the test is not parameterised, return a list containing only the test itself.
        If the test is parameterised incorrectly, for example the number of
        items don't match across occurrences of `each` in the test signature,
        then a `ParameterisationError` is raised.
        """
        if not self.is_parameterised:
            return [self]

        number_of_instances = self.find_number_of_instances()

        generated_tests = []
        for instance_index in range(number_of_instances):
            generated_test = Test(
                fn=self.fn,
                module_name=self.module_name,
                marker=self.marker,
                description=self.description,
                param_meta=ParamMeta(
                    instance_index=instance_index, group_size=number_of_instances
                ),
                capture_output=self.capture_output,
            )
            generated_tests.append(generated_test)
        return generated_tests

    def find_number_of_instances(self) -> int:
        """
        Returns the number of instances that would be generated for the current
        parameterised test.

        A parameterised test is only valid if every instance of `each` contains
        an equal number of items. If the current test is an invalid parameterisation,
        then a `ParameterisationError` is raised.
        """
        default_args = self.resolver.get_default_args()
        lengths = [len(arg) for _, arg in default_args.items() if isinstance(arg, Each)]
        is_valid = len(set(lengths)) in (0, 1)
        if not is_valid:
            raise ParameterisationError(
                f"The test {self.name}/{self.description} is parameterised incorrectly. "
                f"Please ensure all instances of 'each' in the test signature "
                f"are of equal length."
            )
        if len(lengths) == 0:
            return 1
        else:
            return lengths[0]

    def deps(self) -> Mapping[str, inspect.Parameter]:
        return inspect.signature(self.fn).parameters

    def format_description(self, args: Dict[str, Any]) -> str:
        """
        Applies any necessary string formatting to the description,
        given a dictionary `args` of values that will be injected
        into the test.

        This method will mutate the Test by updating the description.
        Returns the newly updated description.
        """

        format_dict = _FormatDict(**args)
        if not self.description:
            self.description = ""

        try:
            self.description = self.description.format_map(format_dict)
        except ValueError:
            pass

        return self.description


def test(description: str, *args, tags: Optional[List[str]] = None, **kwargs):
    """
    Decorator used to indicate that the function it wraps should be collected by Ward.

    Args:
        description: The description of the test. A format string. Resolve fixtures and default params that are injected
            into the test will also be injected into this description before it gets output in the test report.
            The description can contain basic Markdown syntax (bold, italic, backticks for code, etc.).
        tags: An optional list of strings that will 'tag' the test. Many tests can share the same tag, and these
            tags can be used to group tests in some logical manner (for example: by business domain or test type).
            Tagged tests can be queried using the --tags option.
    """

    def decorator_test(func):
        unwrapped = inspect.unwrap(func)
        module_name: str = unwrapped.__module__
        is_home_module: bool = "." not in module_name
        if is_test_module_name(module_name) and is_home_module:
            force_path: Path = kwargs.get("_force_path")
            if force_path:
                path = force_path.absolute()
            else:
                path = get_absolute_path(unwrapped)

            if hasattr(unwrapped, "ward_meta"):
                unwrapped.ward_meta.description = description
                unwrapped.ward_meta.tags = tags
                unwrapped.ward_meta.path = path
            else:
                unwrapped.ward_meta = CollectionMetadata(
                    description=description,
                    tags=tags,
                    path=path,
                )

            collect_into = kwargs.get("_collect_into", COLLECTED_TESTS)
            collect_into[path].append(unwrapped)

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return func

    return decorator_test


class TestOutcome(Enum):
    """
    Enumeration representing all possible outcomes of an attempt at running a test.

    Attributes:
        PASS: Represents a passing test outcome - no errors raised, no assertions failed, the test ran to completion.
        FAIL: The test failed in some way - e.g. an assertion failed or an exception was raised.
        SKIP: The test was skipped.
        XFAIL: The test was expected to fail, and it did fail.
        XPASS: The test was expected to fail, however it unexpectedly passed.
        DRYRUN: The test was not executed because the test session was a dry-run.
    """

    PASS = auto()
    FAIL = auto()
    SKIP = auto()
    XFAIL = auto()  # expected fail
    XPASS = auto()  # unexpected pass
    DRYRUN = auto()  # tests arent executed during dryruns

    @property
    def display_char(self):
        display_chars = {
            TestOutcome.PASS: ".",
            TestOutcome.FAIL: "F",
            TestOutcome.SKIP: "-",
            TestOutcome.XPASS: "U",
            TestOutcome.XFAIL: "x",
            TestOutcome.DRYRUN: ".",
        }
        assert len(display_chars) == len(TestOutcome)
        return display_chars[self]

    @property
    def display_name(self):
        display_names = {
            TestOutcome.PASS: "Passes",
            TestOutcome.FAIL: "Failures",
            TestOutcome.SKIP: "Skips",
            TestOutcome.XPASS: "Unexpected Passes",
            TestOutcome.XFAIL: "Expected Failures",
            TestOutcome.DRYRUN: "Dry-runs",
        }
        assert len(display_names) == len(TestOutcome)
        return display_names[self]

    @property
    def will_fail_session(self) -> bool:
        return self in {TestOutcome.FAIL, TestOutcome.XPASS}

    @property
    def wont_fail_session(self) -> bool:
        return not self.will_fail_session


@dataclass
class TestResult:
    """
    Represents the result of a single test, and contains data that may have been generated as
    part of the execution of that test (for example captured stdout and exceptions that were raised).

    Attributes:
        test: The test corresponding to this result.
        outcome: The outcome of the test: did it pass, fail, get skipped, etc.
        error: If an exception was raised during test execution, it is stored here.
        message: An arbitrary message that can be associated with the result. Generally empty.
        captured_stdout: A string containing anything that was written to stdout during the execution of the test.
        captured_stderr: A string containing anything that was written to stderr during the execution of the test.
    """

    test: Test
    outcome: TestOutcome
    error: Optional[Exception] = None
    message: str = ""
    captured_stdout: str = ""
    captured_stderr: str = ""


def fixtures_used_directly_by_tests(
    tests: Iterable["Test"],
) -> Mapping[Fixture, Collection["Test"]]:
    test_to_fixtures = {t: t.resolver.fixtures for t in tests}

    fixture_to_tests = collections.defaultdict(list)
    for test, used_fixtures in test_to_fixtures.items():
        for fix in used_fixtures.values():
            fixture_to_tests[fix].append(test)

    return fixture_to_tests


@dataclass
class TestArgumentResolver:
    test: "Test"
    iteration: int

    def resolve_args(self, cache: FixtureCache) -> Dict[str, Any]:
        """
        Resolve fixtures and return the resultant name -> Fixture dict.
        If the argument is not a fixture, the raw argument will be used.
        Resolved values will be stored in fixture_cache, accessible
        using the fixture cache key (See `Fixture.key`).
        """
        if self.test.capture_output:
            with redirect_stdout(self.test.sout), redirect_stderr(self.test.serr):
                return self._resolve_args(cache)
        else:
            return self._resolve_args(cache)

    def _resolve_args(self, cache: FixtureCache) -> Dict[str, Any]:
        args_for_iteration = self._get_args_for_iteration()
        resolved_args: Dict[str, Any] = {}
        for name, arg in args_for_iteration.items():
            if is_fixture(arg):
                resolved = self._resolve_single_arg(arg, cache)
            else:
                resolved = arg
            resolved_args[name] = resolved
        return self._unpack_resolved(resolved_args)

    def _get_args_for_iteration(self):
        if not self.test.has_deps:
            return {}
        default_args = self.get_default_args()
        args_for_iteration: Dict[str, Any] = {}
        for name, arg in default_args.items():
            # In the case of parameterised testing, grab the arg corresponding
            # to the current iteration of the parameterised group of tests.
            if isinstance(arg, Each):
                arg = arg[self.iteration]
            args_for_iteration[name] = arg
        return args_for_iteration

    @property
    def fixtures(self) -> Dict[str, Fixture]:
        return {
            name: Fixture(arg)
            for name, arg in self._get_args_for_iteration().items()
            if is_fixture(arg)
        }

    def get_default_args(
        self, func: Optional[Union[Callable, Fixture]] = None
    ) -> Dict[str, Any]:
        """
        Returns a mapping of test argument names to values.

        This method does no fixture resolution.

        If a value is a fixture function, then the raw fixture
        function is returned as a value in the dict, *not* the `Fixture` object.
        """
        fn = func or self.test.fn
        meta = getattr(fn, "ward_meta", None)
        signature = inspect.signature(fn)

        # Override the signature if @using is present
        if meta:
            bound_args = getattr(fn.ward_meta, "bound_args", None)
            if bound_args:
                bound_args.apply_defaults()
                return bound_args.arguments

        default_binding = signature.bind_partial()
        default_binding.apply_defaults()
        return default_binding.arguments

    def _resolve_single_arg(
        self, arg: Callable, cache: FixtureCache
    ) -> Union[Any, Fixture]:
        """
        Get the fixture return value

        If the fixture has been cached, return the value from the cache.
        Otherwise, call the fixture function and return the value.
        """

        if not hasattr(arg, "ward_meta"):
            return arg

        fixture = Fixture(arg)
        if cache.contains(
            fixture, fixture.scope, self.test.scope_key_from(fixture.scope)
        ):
            return cache.get(
                fixture.key, fixture.scope, self.test.scope_key_from(fixture.scope)
            )

        children_defaults = self.get_default_args(func=arg)
        children_resolved = {}
        for name, child_fixture in children_defaults.items():
            child_resolved = self._resolve_single_arg(child_fixture, cache)
            children_resolved[name] = child_resolved

        try:
            args_to_inject = self._unpack_resolved(children_resolved)
            if fixture.is_generator_fixture:
                fixture.gen = arg(**args_to_inject)
                fixture.resolved_val = next(fixture.gen)
            elif fixture.is_async_generator_fixture:
                fixture.gen = arg(**args_to_inject)
                awaitable = fixture.gen.__anext__()
                fixture.resolved_val = asyncio.get_event_loop().run_until_complete(
                    awaitable
                )
            elif fixture.is_coroutine_fixture:
                fixture.resolved_val = asyncio.get_event_loop().run_until_complete(
                    arg(**args_to_inject)
                )
            else:
                fixture.resolved_val = arg(**args_to_inject)
        except (Exception, SystemExit) as e:
            raise FixtureError(f"Unable to resolve fixture '{fixture.name}'") from e
        scope_key = self.test.scope_key_from(fixture.scope)
        cache.cache_fixture(fixture, scope_key)
        return fixture

    @staticmethod
    def _unpack_resolved(fixture_dict: Dict[str, Any]) -> Dict[str, Any]:
        resolved_vals = {}
        for (k, arg) in fixture_dict.items():
            if isinstance(arg, Fixture):
                resolved_vals[k] = arg.resolved_val
            else:
                resolved_vals[k] = arg
        return resolved_vals
