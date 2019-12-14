import functools
import inspect
import uuid
from collections import defaultdict
from contextlib import closing, redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from enum import auto, Enum
from io import StringIO
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Dict, List, Optional, Any, Tuple, Union

from ward.errors import FixtureError, ParameterisationError
from ward.fixtures import Fixture, FixtureCache, ScopeKey
from ward.models import Marker, SkipMarker, XfailMarker, WardMeta, Scope


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
    def path(self) -> Path:
        return self.fn.ward_meta.path

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

    def resolve_args(self, cache: FixtureCache, iteration: int = 0) -> Dict[str, Any]:
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
            return self._unpack_resolved(resolved_args)

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

    def _get_default_args(
        self, func: Optional[Union[Callable, Fixture]] = None
    ) -> Dict[str, Any]:
        """
        Returns a mapping of test argument names to values.

        This method does no fixture resolution.

        If a value is a fixture function, then the raw fixture
        function is returned as a value in the dict, *not* the `Fixture` object.
        """
        fn = func or self.fn
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
        if cache.contains(fixture, fixture.scope, self.scope_key_from(fixture.scope)):
            return cache.get(
                fixture.key, fixture.scope, self.scope_key_from(fixture.scope)
            )

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
            scope_key = self.scope_key_from(fixture.scope)
            cache.cache_fixture(fixture, scope_key)
            return fixture

        children_defaults = self._get_default_args(func=arg)
        children_resolved = {}
        for name, child_fixture in children_defaults.items():
            child_resolved = self._resolve_single_arg(child_fixture, cache)
            children_resolved[name] = child_resolved

        try:
            args_to_inject = self._unpack_resolved(children_resolved)
            if is_generator:
                fixture.gen = arg(**args_to_inject)
                fixture.resolved_val = next(fixture.gen)
            else:
                fixture.resolved_val = arg(**args_to_inject)
        except Exception as e:
            raise FixtureError(f"Unable to resolve fixture '{fixture.name}'") from e
        scope_key = self.scope_key_from(fixture.scope)
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

    def format_description(self, arg_map: Dict[str, Any]) -> str:
        """
        Applies any necessary string formatting to the description,
        given a dictionary `arg_map` of values that will be injected
        into the test.

        This method will mutate the Test by updating the description.
        Returns the newly updated description.
        """
        format_dict = FormatDict(**arg_map)
        if not self.description:
            self.description = ""

        try:
            self.description = self.description.format_map(format_dict)
        except ValueError:
            pass

        return self.description


# Tests declared with the name _, and with the @test decorator
# have to be stored in here, so that they can later be retrieved.
# They cannot be retrieved directly from the module due to name
# clashes. When we're later looking for tests inside the module,
# we can retrieve any anonymous tests from this dict.
anonymous_tests: Dict[str, List[Callable]] = defaultdict(list)


def test(description: str, *args, **kwargs):
    def decorator_test(func):
        mod_name = func.__module__

        force_path = kwargs.get("_force_path")
        if force_path:
            path = force_path
        else:
            path = Path(inspect.getfile(inspect.unwrap(func))).absolute()

        if hasattr(func, "ward_meta"):
            func.ward_meta.description = description
            func.ward_meta.path = path
        else:
            func.ward_meta = WardMeta(description=description, path=path)

        collect_into = kwargs.get("_collect_into")
        if collect_into is not None:
            collect_into[mod_name].append(func)
        else:
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
