---
path: "/modules/ward.test_result"
title: "ward.test_result"
section: "modules"
---

Module ward.test_result
=======================

#### Classes

`TestOutcome(*args, **kwargs)`
:   An enumeration.

    ### Class variables

```python

`FAIL`
:   An enumeration.

```

```python

`PASS`
:   An enumeration.

```

```python

`SKIP`
:   An enumeration.

```

```python

`XFAIL`
:   An enumeration.

```

```python

`XPASS`
:   An enumeration.

```

`TestResult(test, outcome, error=None, message='', captured_stdout='', captured_stderr='')`
:   TestResult(test: ward.testing.Test, outcome: ward.test_result.TestOutcome, error: Union[Exception, NoneType] = None, message: str = '', captured_stdout: str = '', captured_stderr: str = '')

    ### Class variables

```python

`captured_stderr`
:   str(object='') -> str
    str(bytes_or_buffer[, encoding[, errors]]) -> str
    
    Create a new string object from the given object. If encoding or
    errors is specified, then the object must expose a data buffer
    that will be decoded using the given encoding and error handler.
    Otherwise, returns the result of object.__str__() (if defined)
    or repr(object).
    encoding defaults to sys.getdefaultencoding().
    errors defaults to 'strict'.

```

```python

`captured_stdout`
:   str(object='') -> str
    str(bytes_or_buffer[, encoding[, errors]]) -> str
    
    Create a new string object from the given object. If encoding or
    errors is specified, then the object must expose a data buffer
    that will be decoded using the given encoding and error handler.
    Otherwise, returns the result of object.__str__() (if defined)
    or repr(object).
    encoding defaults to sys.getdefaultencoding().
    errors defaults to 'strict'.

```

```python

`error`
:   

```

```python

`message`
:   str(object='') -> str
    str(bytes_or_buffer[, encoding[, errors]]) -> str
    
    Create a new string object from the given object. If encoding or
    errors is specified, then the object must expose a data buffer
    that will be decoded using the given encoding and error handler.
    Otherwise, returns the result of object.__str__() (if defined)
    or repr(object).
    encoding defaults to sys.getdefaultencoding().
    errors defaults to 'strict'.

```