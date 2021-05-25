from tests.test_testing import FALSY_PREDICATES, TRUTHY_PREDICATES
from ward import each, raises, test
from ward._errors import FixtureError
from ward.models import Scope, SkipMarker, XfailMarker


@test("Scope.from_str('{string}') returns {scope}")
def _(
    scope=each(Scope.Test, Scope.Module, Scope.Global),
    string=each("test", "module", "global"),
):
    assert Scope.from_str(string) == scope


@test("Scope.from_str raised FixtureError for invalid fixture string name")
def _(
    arg=each("invalid-scope", 123),
    expected_cause_ex_type=each(KeyError, AttributeError),
):
    with raises(FixtureError) as fixture_error:
        Scope.from_str(arg)
    assert type(fixture_error.raised.__cause__) is expected_cause_ex_type


@test("SkipMarker.active returns True when predicate evaluates to True")
def _(when=TRUTHY_PREDICATES):
    skip_marker = SkipMarker(when=when)
    assert skip_marker.active


@test("SkipMarker.active returns False when predicate evaluates to False")
def _(when=FALSY_PREDICATES):
    skip_marker = SkipMarker(when=when)
    assert not skip_marker.active


@test("XfailMarker.active returns True when predicate evaluates to True")
def _(when=TRUTHY_PREDICATES):
    xfail_marker = XfailMarker(when=when)
    assert xfail_marker.active


@test("XfailMarker.active returns False when predicate evaluates to False")
def _(when=FALSY_PREDICATES):
    xfail_marker = XfailMarker(when=when)
    assert not xfail_marker.active
