---
path: "/modules/ward.fixtures"
title: "ward.fixtures"
section: "modules"
---

Module ward.fixtures
====================

#### Functions

```python
    
`fixture(func=None, *, description=None)`
:   
```

#### Classes

`CollectionError(*args, **kwargs)`
:   Common base class for all non-exit exceptions.

`Fixture(fn)`
:   Fixture(fn: Callable)

    ### Instance variables

```python

`is_generator_fixture`
:   

```

```python

`key`
:   

```

```python

`name`
:   

```

    ### Methods

```python

```python
    
`deps(self)`
:   
```

```

```python

```python
    
`teardown(self)`
:   
```

```

`FixtureCache()`
:   FixtureCache(_fixtures: Dict[str, ward.fixtures.Fixture] = <factory>)

    ### Methods

```python

```python
    
`cache_fixture(self, fixture)`
:   
```

```

```python

```python
    
`teardown_all(self)`
:   Run the teardown code for all generator fixtures in the cache
```

```

`FixtureExecutionError(*args, **kwargs)`
:   Common base class for all non-exit exceptions.

`TestSetupError(*args, **kwargs)`
:   Common base class for all non-exit exceptions.

    ### Descendants

    * ward.fixtures.CollectionError