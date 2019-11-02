---
path: "/modules/ward.fixtures"
title: "ward.fixtures"
section: "modules"
---

## Functions

```python
fixture(func=None, *, description=None)
```

## Classes

### Class `CollectionError`

```python
CollectionError (*args, **kwargs)
```

Common base class for all non-exit exceptions.

[]

### Class `Fixture`

```python
Fixture (fn)
```

Fixture(fn: Callable)

[<Variable 'ward.fixtures.Fixture.is_generator_fixture'>, <Variable 'ward.fixtures.Fixture.key'>, <Variable 'ward.fixtures.Fixture.name'>]

#### Instance variables

* `is_generator_fixture` Docstring 
* `key` Docstring 
* `name` Docstring 

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
teardown_all(self)
```
Run the teardown code for all generator fixtures in the cache

### Class `FixtureExecutionError`

```python
FixtureExecutionError (*args, **kwargs)
```

Common base class for all non-exit exceptions.

[]

### Class `TestSetupError`

```python
TestSetupError (*args, **kwargs)
```

Common base class for all non-exit exceptions.

#### Descendants

* `ward.fixtures.CollectionError`
[]