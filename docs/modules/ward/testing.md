---
path: "/modules/ward.testing"
title: "ward.testing"
section: "modules"
---

## Functions

```python
skip(func_or_reason=None, *, reason: str = None)
```

```python
test(description: str)
```

```python
xfail(func_or_reason=None, *, reason: str = None)
```

## Classes

### Test

```python
Test (fn, module_name, fixture_cache=<factory>, marker=None, description=None)
```

Test(fn: Callable, module_name: str, fixture_cache: ward.fixtures.FixtureCache = <factory>, marker: Union[ward.models.Marker, NoneType] = None, description: Union[str, NoneType] = None)

#### Class variables

* `description` 
* `marker` 

#### Instance variables

* `line_number` 
* `name` 
* `qualified_name` 

#### Methods

```python
deps(self)
```

```python
has_deps(self)
```

```python
resolve_fixtures(self)
```
Resolve fixtures and return the resultant name -> Fixture dict.
Resolved values will be stored in fixture_cache, accessible
using the fixture cache key (See `Fixture.key`).

```python
teardown_fixtures_in_cache(self)
```