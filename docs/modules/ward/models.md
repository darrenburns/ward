---
path: "/modules/ward.models"
title: "ward.models"
section: "modules"
---

Module ward.models
==================

    ### Classes

        
    ```python
    Marker(name: str)
    ```
    Marker(name: str)

    ### Descendants

        * `ward.models.SkipMarker`
        * `ward.models.XfailMarker`

        
    ```python
    SkipMarker(name: str = 'SKIP', reason: Union[str, NoneType] = None)
    ```
    SkipMarker(name: str = 'SKIP', reason: Union[str, NoneType] = None)

    ### Class variables

        
    ```python
    name
    ```
    str(object='') -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object.__str__() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to 'strict'.

        
    ```python
    reason
    ```
    

        
    ```python
    WardMeta(marker: Union[ward.models.Marker, NoneType] = None, description: Union[str, NoneType] = None, is_fixture: bool = False)
    ```
    WardMeta(marker: Union[ward.models.Marker, NoneType] = None, description: Union[str, NoneType] = None, is_fixture: bool = False)

    ### Class variables

        
    ```python
    description
    ```
    

        
    ```python
    is_fixture
    ```
    bool(x) -> bool

Returns True when the argument x is true, False otherwise.
The builtins True and False are the only two instances of the class bool.
The class bool is a subclass of the class int, and cannot be subclassed.

        
    ```python
    marker
    ```
    

        
    ```python
    XfailMarker(name: str = 'XFAIL', reason: Union[str, NoneType] = None)
    ```
    XfailMarker(name: str = 'XFAIL', reason: Union[str, NoneType] = None)

    ### Class variables

        
    ```python
    name
    ```
    str(object='') -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object.__str__() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to 'strict'.

        
    ```python
    reason
    ```