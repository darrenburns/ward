---
path: "/modules/ward.test_result"
title: "ward.test_result"
section: "modules"
type: "apidocs"
---

## Classes

### Class `TestOutcome`

```python
TestOutcome (*args, **kwargs)
```

An enumeration.

#### Class variables

* `FAIL` Docstring An enumeration.
* `PASS` Docstring An enumeration.
* `SKIP` Docstring An enumeration.
* `XFAIL` Docstring An enumeration.
* `XPASS` Docstring An enumeration.
[]

### Class `TestResult`

```python
TestResult (test, outcome, error=None, message='', captured_stdout='', captured_stderr='')
```

TestResult(test: ward.testing.Test, outcome: ward.test_result.TestOutcome, error: Union[Exception, NoneType] = None, message: str = '', captured_stdout: str = '', captured_stderr: str = '')

#### Class variables

* `captured_stderr` Docstring str(object='') -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object.__str__() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to 'strict'.
* `captured_stdout` Docstring str(object='') -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object.__str__() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to 'strict'.
* `error` Docstring 
* `message` Docstring The message that will blah
[]