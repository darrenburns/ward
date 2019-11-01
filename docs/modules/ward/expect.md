---
path: "/modules/ward.expect"
title: "ward.expect"
section: "modules"
---

## Classes

### Class `ExpectationFailed`

```python
ExpectationFailed (message, history)
```

Common base class for all non-exit exceptions.

[]

### Class `Expected`

```python
Expected (this, op, that, op_args, op_kwargs, success=True)
```

Expected(this: Any, op: str, that: Union[Any, NoneType], op_args: Tuple, op_kwargs: Dict, success: bool = True)

#### Class variables

* `success` Docstring bool(x) -> bool

Returns True when the argument x is true, False otherwise.
The builtins True and False are the only two instances of the class bool.
The class bool is a subclass of the class int, and cannot be subclassed.
[]

### Class `expect`

```python
expect (this)
```

[]

#### Methods

```python
approx(self, that: Any, rel_tol: float = 1e-09, abs_tol: float = 0.0)
```

```python
called(self)
```

```python
called_once_with(self, *args, **kwargs)
```

```python
called_with(self, *args, **kwargs)
```

```python
contained_in(self, that: Iterable[Any])
```

```python
contains(self, that: Any)
```

```python
equals(self, expected: Any)
```

```python
greater_than(self, that: Any)
```

```python
greater_than_or_equals(self, that: Any)
```

```python
has_calls(self, calls: List[unittest.mock._Call], any_order: bool = False)
```

```python
has_length(self, length: int)
```

```python
identical_to(self, that: Any)
```

```python
instance_of(self, type: Type)
```

```python
less_than(self, that: Any)
```

```python
less_than_or_equals(self, that: Any)
```

```python
not_approx(self, that: Any, rel_tol: float = 1e-09, abs_tol: float = 0.0)
```

```python
not_called(self)
```

```python
not_contained_in(self, that: Iterable[Any])
```

```python
not_contains(self, that: Any)
```

```python
not_equals(self, that: Any)
```

```python
not_greater_than(self, that: Any)
```

```python
not_greater_than_or_equals(self, that: Any)
```

```python
not_has_length(self, length: int)
```

```python
not_identical_to(self, that: Any)
```

```python
not_instance_of(self, type: Type)
```

```python
not_less_than(self, that: Any)
```

```python
not_less_than_or_equals(self, that: Any)
```

```python
not_satisfies(self, predicate: Callable[[ForwardRef('expect')], bool])
```

```python
satisfies(self, predicate: Callable[[ForwardRef('expect')], bool])
```

### Class `raises`

```python
raises (expected_ex_type)
```

[]