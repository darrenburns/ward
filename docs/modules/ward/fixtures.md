---
path: "/modules/ward.fixtures"
title: "ward.fixtures"
section: "modules"
type: "apidocs"
---

## Functions

```python
fixture(func=None, *, scope: Union[ward.models.Scope, str, NoneType] = <Scope.Test: test'>)
```

## Classes

### Class `Fixture`

```python
Fixture (fn, last_resolved_module_name=None, last_resolved_test_id=None)
```

Fixture(fn: Callable, last_resolved_module_name: Union[str, NoneType] = None, last_resolved_test_id: Union[str, NoneType] = None)

[<Variable 'ward.fixtures.Fixture.is_generator_fixture'>, <Variable 'ward.fixtures.Fixture.key'>, <Variable 'ward.fixtures.Fixture.name'>, <Variable 'ward.fixtures.Fixture.scope'>]

#### Instance variables

* `is_generator_fixture` Docstring 
* `key` Docstring 
* `name` Docstring 
* `scope` Docstring 

#### Methods

```python
deps(self)
```

```python
teardown(self)
```

### Class `FixtureCache`

```python
FixtureCache ()
```

FixtureCache(_fixtures: Dict[str, ward.fixtures.Fixture] = <factory>)

[]

#### Methods

```python
cache_fixture(self, fixture: ward.fixtures.Fixture)
```

```python
get(self, scope: Union[ward.models.Scope, NoneType], module_name: Union[str, NoneType], test_id: Union[str, NoneType])
```

```python
teardown_all(self)
```
Run the teardown code for all generator fixtures in the cache

```python
teardown_fixtures(self, fixtures: List[ward.fixtures.Fixture])
```