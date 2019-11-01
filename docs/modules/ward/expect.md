---
path: "/modules/ward.expect"
title: "ward.expect"
section: "modules"
---

Module ward.expect
==================

#### Classes

`ExpectationFailed(message, history)`
:   Common base class for all non-exit exceptions.

`Expected(this, op, that, op_args, op_kwargs, success=True)`
:   Expected(this: Any, op: str, that: Union[Any, NoneType], op_args: Tuple, op_kwargs: Dict, success: bool = True)

    ### Class variables

```python

`success`
:   bool(x) -> bool
    
    Returns True when the argument x is true, False otherwise.
    The builtins True and False are the only two instances of the class bool.
    The class bool is a subclass of the class int, and cannot be subclassed.

```

`expect(this)`
:   

    ### Methods

```python

```python
    
`approx(self, that, rel_tol=1e-09, abs_tol=0.0)`
:   
```

```

```python

```python
    
`called(self)`
:   
```

```

```python

```python
    
`called_once_with(self, *args, **kwargs)`
:   
```

```

```python

```python
    
`called_with(self, *args, **kwargs)`
:   
```

```

```python

```python
    
`contained_in(self, that)`
:   
```

```

```python

```python
    
`contains(self, that)`
:   
```

```

```python

```python
    
`equals(self, expected)`
:   
```

```

```python

```python
    
`greater_than(self, that)`
:   
```

```

```python

```python
    
`greater_than_or_equals(self, that)`
:   
```

```

```python

```python
    
`has_calls(self, calls, any_order=False)`
:   
```

```

```python

```python
    
`has_length(self, length)`
:   
```

```

```python

```python
    
`identical_to(self, that)`
:   
```

```

```python

```python
    
`instance_of(self, type)`
:   
```

```

```python

```python
    
`less_than(self, that)`
:   
```

```

```python

```python
    
`less_than_or_equals(self, that)`
:   
```

```

```python

```python
    
`not_approx(self, that, rel_tol=1e-09, abs_tol=0.0)`
:   
```

```

```python

```python
    
`not_called(self)`
:   
```

```

```python

```python
    
`not_contained_in(self, that)`
:   
```

```

```python

```python
    
`not_contains(self, that)`
:   
```

```

```python

```python
    
`not_equals(self, that)`
:   
```

```

```python

```python
    
`not_greater_than(self, that)`
:   
```

```

```python

```python
    
`not_greater_than_or_equals(self, that)`
:   
```

```

```python

```python
    
`not_has_length(self, length)`
:   
```

```

```python

```python
    
`not_identical_to(self, that)`
:   
```

```

```python

```python
    
`not_instance_of(self, type)`
:   
```

```

```python

```python
    
`not_less_than(self, that)`
:   
```

```

```python

```python
    
`not_less_than_or_equals(self, that)`
:   
```

```

```python

```python
    
`not_satisfies(self, predicate)`
:   
```

```

```python

```python
    
`satisfies(self, predicate)`
:   
```

```

`raises(expected_ex_type)`
: