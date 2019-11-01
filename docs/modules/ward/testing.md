---
path: "/modules/ward.testing"
title: "ward.testing"
section: "modules"
---

Module ward.testing
===================

#### Functions

```python
    
`skip(func_or_reason=None, *, reason=None)`
:   
```

```python
    
`test(description)`
:   
```

```python
    
`xfail(func_or_reason=None, *, reason=None)`
:   
```

#### Classes

`Test(fn, module_name, fixture_cache=<factory>, marker=None, description=None)`
:   Test(fn: Callable, module_name: str, fixture_cache: ward.fixtures.FixtureCache = <factory>, marker: Union[ward.models.Marker, NoneType] = None, description: Union[str, NoneType] = None)

    ### Class variables

```python

`description`
:   

```

```python

`marker`
:   

```

    ### Instance variables

```python

`line_number`
:   

```

```python

`name`
:   

```

```python

`qualified_name`
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
    
`has_deps(self)`
:   
```

```

```python

```python
    
`resolve_fixtures(self)`
:   Resolve fixtures and return the resultant name -> Fixture dict.
    Resolved values will be stored in fixture_cache, accessible
    using the fixture cache key (See `Fixture.key`).
```

```

```python

```python
    
`teardown_fixtures_in_cache(self)`
:   
```

```