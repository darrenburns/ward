import asyncio
import collections
import functools
import inspect
import traceback
import uuid
from collections import defaultdict
from contextlib import ExitStack, closing, redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from enum import Enum, auto
from io import StringIO
from pathlib import Path
from timeit import default_timer
from types import MappingProxyType
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    Iterable,
    Mapping,
    Collection,
)

from ward.errors import FixtureError, ParameterisationError
from ward.fixtures import Fixture, FixtureCache, ScopeKey, is_fixture
from ward.models import Marker, Scope, SkipMarker, WardMeta, XfailMarker
from ward.util import get_absolute_path


@dataclass
class Each:
    args: Tuple[Any]

    def __getitem__(self, args):
        return self.args[args]

    def __len__(self):
        return len(self.args)


def each(*args):
    return Each(args)


def skip(func_or_reason=None, *, reason: str = None):
    if func_or_reason is None:
        return functools.partial(skip, reason=reason)

    if isinstance(func_or_reason, str):
        return functools.partial(skip, reason=func_or_reason)

    func = func_or_reason
    marker = SkipMarker(reason=reason)
    if hasattr(func, "ward_meta"):
        func.ward_meta.marker = marker
    else:
        func.ward_meta = WardMeta(marker=marker)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def xfail(func_or_reason=None, *, reason: str = None):
    if func_or_reason is None:
        return functools.partial(xfail, reason=reason)

    if isinstance(func_or_reason, str):
        return functools.partial(xfail, reason=func_or_reason)

    func = func_or_reason
    marker = XfailMarker(reason=reason)
    if hasattr(func, "ward_meta"):
        func.ward_meta.marker = marker
    else:
        func.ward_meta = WardMeta(marker=marker)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def generate_id():
    return uuid.uuid4().hex


class FormatDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


@dataclass
class ParamMeta:
    instance_index: int = 0
    group_size: int = 1


@dataclass
class Test:
    """
    A representation of a single Ward test.
    """

    fn: Callable
    module_name: str
    id: str = field(default_factory=generate_id)
    marker: Optional[Marker] = None
    description: Optional[str] = None
    param_meta: Optional[ParamMeta] = field(default_factory=ParamMeta)
    capture_output: bool = True
    sout: StringIO = field(default_factory=StringIO)
    serr: StringIO = field(default_factory=StringIO)
    ward_meta: WardMeta = field(default_factory=WardMeta)
    timer: Optional["Timer"] = None
    tags: List[str] = field(default_factory=list)

    def __hash__(self):
        return hash((self.__class__, self.id))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def run(self, cache: FixtureCache, dry_run=False) -> "TestResult":
        with ExitStack() as stack:
            self.timer = stack.enter_context(Timer())
            if self.capture_output:
                stack.enter_context(redirect_stdout(self.sout))
                stack.enter_context(redirect_stderr(self.serr))

            if dry_run:
                with closing(self.sout), closing(self.serr):
                    result = TestResult(self, TestOutcome.DRYRUN)
                return result

            if isinstance(self.marker, SkipMarker):
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
            except (Exception, SystemExit) as e:
                outcome = (
                    TestOutcome.XFAIL
                    if isinstance(self.marker, XfailMarker)
                    else TestOutcome.FAIL
                )
                error = e
            else:
                outcome = (
                    TestOutcome.XPASS
                    if isinstance(self.marker, XfailMarker)
                    else TestOutcome.PASS
                )
                error = None

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
        return self.fn.__name__

    @property
    def path(self) -> Path:
        return self.fn.ward_meta.path

    @property
    def qualified_name(self) -> str:
        name = self.name or ""
        return f"{self.module_name}.{name}"

    @property
    def is_async_test(self) -> bool:
        return inspect.iscoroutinefunction(inspect.unwrap(self.fn))

    @property
    def line_number(self) -> int:
        return inspect.getsourcelines(self.fn)[1]

    @property
    def has_deps(self) -> bool:
        return len(self.deps()) > 0

    @property
    def is_parameterised(self) -> bool:
        """
        Return `True` if a test is parameterised, `False` otherwise.
        A test is considered parameterised if any of its default arguments
        have a value that is an instance of `Each`.
        """
        default_args = self.resolver._get_default_args()
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

        number_of_instances = self._find_number_of_instances()

        generated_tests = []
        for instance_index in range(number_of_instances):
            test = Test(
                fn=self.fn,
                module_name=self.module_name,
                marker=self.marker,
                description=self.description,
                param_meta=ParamMeta(
                    instance_index=instance_index, group_size=number_of_instances
                ),
                capture_output=self.capture_output,
            )
            generated_tests.append(test)
        return generated_tests

    def _find_number_of_instances(self) -> int:
        """
        Returns the number of instances that would be generated for the current
        parameterised test.

        A parameterised test is only valid if every instance of `each` contains
        an equal number of items. If the current test is an invalid parameterisation,
        then a `ParameterisationError` is raised.
        """
        default_args = self.resolver._get_default_args()
        lengths = [len(arg) for _, arg in default_args.items() if isinstance(arg, Each)]
        is_valid = len(set(lengths)) in (0, 1)
        if not is_valid:
            raise ParameterisationError(
                f"The test {self.name}/{self.description} is parameterised incorrectly. "
                f"Please ensure all instances of 'each' in the test signature "
                f"are of equal length."
            )
        return lengths[0]

    def deps(self) -> MappingProxyType:
        return inspect.signature(self.fn).parameters

    def format_description(self, args: Dict[str, Any]) -> str:
        """
        Applies any necessary string formatting to the description,
        given a dictionary `args` of values that will be injected
        into the test.

        This method will mutate the Test by updating the description.
        Returns the newly updated description.
        """

        format_dict = FormatDict(**args)
        if not self.description:
            self.description = ""

        try:
            self.description = self.description.format_map(format_dict)
        except ValueError:
            pass

        return self.description


@dataclass
class TestArgumentResolver:
    test: Test
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
        default_args = self._get_default_args()
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

    def _get_default_args(
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

        has_deps = len(fixture.deps()) > 0
        if not has_deps:
            try:
                if fixture.is_generator_fixture:
                    fixture.gen = arg()
                    fixture.resolved_val = next(fixture.gen)
                elif fixture.is_async_generator_fixture:
                    fixture.gen = arg()
                    awaitable = fixture.gen.__anext__()
                    fixture.resolved_val = asyncio.get_event_loop().run_until_complete(
                        awaitable
                    )
                elif fixture.is_coroutine_fixture:
                    fixture.resolved_val = asyncio.get_event_loop().run_until_complete(
                        arg()
                    )
                else:
                    fixture.resolved_val = arg()
            except (Exception, SystemExit) as e:
                raise FixtureError(f"Unable to resolve fixture '{fixture.name}'") from e
            scope_key = self.test.scope_key_from(fixture.scope)
            cache.cache_fixture(fixture, scope_key)
            return fixture

        children_defaults = self._get_default_args(func=arg)
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

    def _unpack_resolved(self, fixture_dict: Dict[str, Any]) -> Dict[str, Any]:
        resolved_vals = {}
        for (k, arg) in fixture_dict.items():
            if isinstance(arg, Fixture):
                resolved_vals[k] = arg.resolved_val
            else:
                resolved_vals[k] = arg
        return resolved_vals


def fixtures_used_directly_by_tests(
        tests: Iterable[Test],
) -> Mapping[Fixture, Collection[Test]]:
    test_to_fixtures = {test: test.resolver.fixtures for test in tests}

    fixture_to_tests = collections.defaultdict(list)
    for test, used_fixtures in test_to_fixtures.items():
        for fix in used_fixtures.values():
            fixture_to_tests[fix].append(test)

    return fixture_to_tests


def is_test_module_name(module_name: str) -> bool:
    return module_name.startswith("test_") or module_name.endswith("_test")


# Tests declared with the name _, and with the @test decorator
# have to be stored in here, so that they can later be retrieved.
# They cannot be retrieved directly from the module due to name
# clashes. When we're later looking for tests inside the module,
# we can retrieve any anonymous tests from this dict.
# Map of module absolute Path to list of tests in the module
anonymous_tests: Dict[Path, List[Callable]] = defaultdict(list)


def test(description: str, *args, tags=None, **kwargs):
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
                unwrapped.ward_meta = WardMeta(
                    description=description, tags=tags, path=path,
                )

            collect_into = kwargs.get("_collect_into", anonymous_tests)
            collect_into[path].append(unwrapped)

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return func

    return decorator_test


class TestOutcome(Enum):
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


@dataclass
class TestResult:
    test: Test
    outcome: TestOutcome
    error: Optional[Exception] = None
    message: str = ""
    captured_stdout: str = ""
    captured_stderr: str = ""


class Timer:
    def __init__(self):
        self._start_time = None
        self.duration = None

    def __enter__(self):
        self._start_time = default_timer()
        return self

    def __exit__(self, *args):
        self.duration = default_timer() - self._start_time
