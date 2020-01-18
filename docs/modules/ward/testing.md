---
path: "/modules/ward.testing"
title: "ward.testing"
section: "modules"
type: "apidocs"
---

## Functions

```python
generate_id()
```

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

### Class `Test`

```python
Test (fn, module_name, id=<factory>, marker=None, description=None)
```

A representation of a single Ward test.

#### Class variables

* `description` Docstring 
* `marker` Docstring 
[<Variable 'ward.testing.Test.line_number'>, <Variable 'ward.testing.Test.name'>, <Variable 'ward.testing.Test.qualified_name'>]

#### Instance variables

* `line_number` Docstring 
* `name` Docstring 
* `qualified_name` Docstring 

#### Methods

```python
deps(self)
```

```python
has_deps(self)
```

```python
resolve_fixtures(self, cache: ward.fixtures.FixtureCache)
```
Resolve fixtures and return the resultant name -> Fixture dict.
Resolved values will be stored in fixture_cache, accessible
using the fixture cache key (See `Fixture.key`).