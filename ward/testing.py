import functools
import inspect
import uuid
from collections import defaultdict
from contextlib import closing, redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from enum import Enum, auto
from io import StringIO
from types import MappingProxyType
from typing import Callable, Dict, List, Optional, Any, Tuple, Union

from ward.errors import FixtureError, ParameterisationError
from ward.fixtures import Fixture, FixtureCache, Scope
from ward.models import Marker, SkipMarker, XfailMarker, WardMeta


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
    param_meta: Optional[ParamMeta] = ParamMeta()
    sout: StringIO = field(default_factory=StringIO)
    serr: StringIO = field(default_factory=StringIO)

    def __call__(self, *args, **kwargs):
        with redirect_stdout(self.sout), redirect_stderr(self.serr):
            return self.fn(*args, **kwargs)

    @property
    def name(self):
        return self.fn.__name__

    @property
    def qualified_name(self):
        name = self.name or ""
        return f"{self.module_name}.{name}"

    @property
    def line_number(self):
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
        default_args = self._get_default_args()
        return any(isinstance(arg, Each) for arg in default_args.values())

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
            generated_tests.append(
                Test(
                    fn=self.fn,
                    module_name=self.module_name,
                    marker=self.marker,
                    description=self.description,
                    param_meta=ParamMeta(
                        instance_index=instance_index, group_size=number_of_instances
                    ),
                )
            )
        return generated_tests

    def deps(self) -> MappingProxyType:
        return inspect.signature(self.fn).parameters

    def resolve_args(self, cache: FixtureCache, iteration: int) -> Dict[str, Any]:
        """
        Resolve fixtures and return the resultant name -> Fixture dict.
        If the argument is not a fixture, the raw argument will be used.
        Resolved values will be stored in fixture_cache, accessible
        using the fixture cache key (See `Fixture.key`).
        """
        with redirect_stdout(self.sout), redirect_stderr(self.serr):
            if not self.has_deps:
                return {}

            default_args = self._get_default_args()

            resolved_args: Dict[str, Any] = {}
            for name, arg in default_args.items():
                # In the case of parameterised testing, grab the arg corresponding
                # to the current iteration of the parameterised group of tests.
                if isinstance(arg, Each):
                    arg = arg[iteration]
                if hasattr(arg, "ward_meta") and arg.ward_meta.is_fixture:
                    resolved = self._resolve_single_arg(arg, cache)
                else:
                    resolved = arg
                resolved_args[name] = resolved
            return self._resolve_fixture_values(resolved_args)

    def get_result(self, outcome, exception=None):
        with closing(self.sout), closing(self.serr):
            if outcome in (TestOutcome.PASS, TestOutcome.SKIP):
                result = TestResult(self, outcome)
            else:
                result = TestResult(
                    self,
                    outcome,
                    exception,
                    captured_stdout=self.sout.getvalue(),
                    captured_stderr=self.serr.getvalue(),
                )
            return result

    def _get_default_args(self) -> Dict[str, Any]:
        """
        Returns a mapping of test argument names to values. This method does no
        fixture resolution. If a value is a fixture function, then the raw fixture
        function is used, *not* the `Fixture` object.
        """
        signature = inspect.signature(self.fn)
        default_binding = signature.bind_partial()
        default_binding.apply_defaults()
        return default_binding.arguments

    def _find_number_of_instances(self) -> int:
        """
        Returns the number of instances that would be generated for the current
        parameterised test.

        A parameterised test is only valid if every instance of `each` contains
        an equal number of items. If the current test is an invalid parameterisation,
        then a `ParameterisationError` is raised.
        """
        default_args = self._get_default_args()
        lengths = [len(arg) for _, arg in default_args.items() if isinstance(arg, Each)]
        is_valid = len(set(lengths)) in (0, 1)
        if not is_valid:
            raise ParameterisationError(
                f"The test {self.name}/{self.description} is parameterised incorrectly. "
                f"Please ensure all instances of 'each' in the test signature "
                f"are of equal length."
            )
        return lengths[0]

    def _resolve_single_arg(
        self, arg: Callable, cache: FixtureCache
    ) -> Union[Any, Fixture]:
        if not hasattr(arg, "ward_meta"):
            return arg

        fixture = Fixture(arg)
        if fixture.key in cache:
            cached_fixture = cache[fixture.key]
            if fixture.scope == Scope.Global:
                return cached_fixture
            elif fixture.scope == Scope.Module:
                if cached_fixture.last_resolved_module_name == self.module_name:
                    return cached_fixture
            elif fixture.scope == Scope.Test:
                if cached_fixture.last_resolved_test_id == self.id:
                    return cached_fixture

        # Cache miss, so update the fixture metadata before we resolve and cache it
        fixture.last_resolved_test_id = self.id
        fixture.last_resolved_module_name = self.module_name

        has_deps = len(fixture.deps()) > 0
        is_generator = fixture.is_generator_fixture
        if not has_deps:
            try:
                if is_generator:
                    fixture.gen = arg()
                    fixture.resolved_val = next(fixture.gen)
                else:
                    fixture.resolved_val = arg()
            except Exception as e:
                raise FixtureError(f"Unable to resolve fixture '{fixture.name}'") from e
            cache.cache_fixture(fixture)
            return fixture

        signature = inspect.signature(arg)
        children_defaults = signature.bind_partial()
        children_defaults.apply_defaults()
        children_resolved = {}
        for name, child_fixture in children_defaults.arguments.items():
            child_resolved = self._resolve_single_arg(child_fixture, cache)
            children_resolved[name] = child_resolved
        try:
            if is_generator:
                fixture.gen = arg(**self._resolve_fixture_values(children_resolved))
                fixture.resolved_val = next(fixture.gen)
            else:
                fixture.resolved_val = arg(
                    **self._resolve_fixture_values(children_resolved)
                )
        except Exception as e:
            raise FixtureError(f"Unable to resolve fixture '{fixture.name}'") from e
        cache.cache_fixture(fixture)
        return fixture

    def _resolve_fixture_values(self, fixture_dict: Dict[str, Any]) -> Dict[str, Any]:
        resolved_vals = {}
        for (k, arg) in fixture_dict.items():
            if isinstance(arg, Fixture):
                resolved_vals[k] = arg.resolved_val
            else:
                resolved_vals[k] = arg
        return resolved_vals


# Tests declared with the name _, and with the @test decorator
# have to be stored in here, so that they can later be retrieved.
# They cannot be retrieved directly from the module due to name
# clashes. When we're later looking for tests inside the module,
# we can retrieve any anonymous tests from this dict.
anonymous_tests: Dict[str, List[Callable]] = defaultdict(list)


def test(description: str):
    def decorator_test(func):
        if func.__name__ == "_":
            mod_name = func.__module__
            if hasattr(func, "ward_meta"):
                func.ward_meta.description = description
            else:
                func.ward_meta = WardMeta(description=description)
            anonymous_tests[mod_name].append(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator_test


class TestOutcome(Enum):
    PASS = auto()
    FAIL = auto()
    SKIP = auto()
    XFAIL = auto()  # expected fail
    XPASS = auto()  # unexpected pass


@dataclass
class TestResult:
    test: Test
    outcome: TestOutcome
    error: Optional[Exception] = None
    message: str = ""
    captured_stdout: str = ""
    captured_stderr: str = ""
