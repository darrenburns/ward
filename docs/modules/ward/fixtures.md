---
path: "/modules/ward.fixtures"
title: "ward.fixtures"
section: "modules"
---

Module ward.fixtures
====================

### Functions

```python
fixture(func=None, *, description=None)
```

### Classes

```python
CollectionError(*args, **kwargs)
```
Common base class for all non-exit exceptions.

```python
Fixture(fn: Callable)
```
Fixture(fn: Callable)

#### Instance variables

* `is_generator_fixture` 

* `key` 

* `name` 

#### Methods

```python
deps(self)
```

```python
teardown(self)
```

```python
FixtureCache()
```
FixtureCache(_fixtures: Dict[str, ward.fixtures.Fixture] = <factory>)

#### Methods

```python
cache_fixture(self, fixture: ward.fixtures.Fixture)
```

```python
teardown_all(self)
```
Run the teardown code for all generator fixtures in the cache

```python
FixtureExecutionError(*args, **kwargs)
```
Common base class for all non-exit exceptions.

```python
TestSetupError(*args, **kwargs)
```
Common base class for all non-exit exceptions.

#### Descendants

* `ward.fixtures.CollectionError`
