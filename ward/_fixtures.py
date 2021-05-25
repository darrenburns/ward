from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Collection, Dict, Iterable, Mapping, Tuple, Union

from ward.fixtures import Fixture
from ward.models import Scope

FixtureKey = str
TestId = str
ScopeKey = Union[TestId, Path, Scope]
ScopeCache = Dict[Scope, Dict[ScopeKey, Dict[FixtureKey, Fixture]]]


def _scope_cache_factory():
    return {scope: {} for scope in Scope}


@dataclass
class FixtureCache:
    """
    A collection of caches, each storing data for a different scope.

    When a fixture is resolved, it is stored in the appropriate cache given
    the scope of the fixture.

    A lookup into this cache is a 3 stage process:

    Scope -> ScopeKey -> FixtureKey

    The first 2 lookups (Scope and ScopeKey) let us determine:
        e.g. has a test-scoped fixture been cached for the current test?
        e.g. has a module-scoped fixture been cached for the current test module?

    The final lookup lets us retrieve the actual fixture given a fixture key.
    """

    _scope_cache: ScopeCache = field(default_factory=_scope_cache_factory)

    def _get_subcache(self, scope: Scope) -> Dict[str, Any]:
        return self._scope_cache[scope]

    def get_fixtures_at_scope(
        self, scope: Scope, scope_key: ScopeKey
    ) -> Dict[FixtureKey, Fixture]:
        subcache = self._get_subcache(scope)
        if scope_key not in subcache:
            subcache[scope_key] = {}
        return subcache.get(scope_key)

    def cache_fixture(self, fixture: Fixture, scope_key: ScopeKey):
        """
        Cache a fixture at the appropriate scope for the given test.
        """
        fixtures = self.get_fixtures_at_scope(fixture.scope, scope_key)
        fixtures[fixture.key] = fixture

    def teardown_fixtures_for_scope(self, scope: Scope, scope_key: ScopeKey):
        fixture_dict = self.get_fixtures_at_scope(scope, scope_key)
        fixtures = list(fixture_dict.values())
        for fixture in fixtures:
            with suppress(RuntimeError, StopIteration):
                fixture.teardown()
            del fixture_dict[fixture.key]

    def teardown_global_fixtures(self):
        self.teardown_fixtures_for_scope(Scope.Global, Scope.Global)

    def contains(self, fixture: Fixture, scope: Scope, scope_key: ScopeKey) -> bool:
        fixtures = self.get_fixtures_at_scope(scope, scope_key)
        return fixture.key in fixtures

    def get(
        self, fixture_key: FixtureKey, scope: Scope, scope_key: ScopeKey
    ) -> Fixture:
        fixtures = self.get_fixtures_at_scope(scope, scope_key)
        return fixtures.get(fixture_key)


def is_fixture(obj: Any) -> bool:
    """
    Returns True if and only if the object is a fixture function
    (it would be False for a Fixture instance,
    but True for the underlying function inside it).
    """
    return hasattr(obj, "ward_meta") and obj.ward_meta.is_fixture


FixtureHierarchyMapping = Mapping[Fixture, Collection[Fixture]]


def fixture_parents_and_children(
    fixtures: Iterable[Fixture],
) -> Tuple[FixtureHierarchyMapping, FixtureHierarchyMapping]:
    """
    Given an iterable of Fixtures, produce two dictionaries:
    the first maps each fixture to its parents (the fixtures it depends on);
    the second maps each fixture to its children (the fixtures that depend on it).
    """
    fixtures_to_parents = {fixture: fixture.parents() for fixture in fixtures}

    # not a defaultdict, because we want to have empty entries if no parents when we return
    fixtures_to_children = {fixture: [] for fixture in fixtures}
    for fixture, parents in fixtures_to_parents.items():
        for parent in parents:
            fixtures_to_children[parent].append(fixture)

    return fixtures_to_parents, fixtures_to_children
