Module ward.expect
==================

Classes
-------

`ExpectationFailed(message, history)`
:   Common base class for all non-exit exceptions.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException

`Expected(this, op, that, op_args, op_kwargs, success=True)`
:   Expected(this: Any, op: str, that: Union[Any, NoneType], op_args: Tuple, op_kwargs: Dict, success: bool = True)

    ### Class variables

    `success`
    :   bool(x) -> bool
        
        Returns True when the argument x is true, False otherwise.
        The builtins True and False are the only two instances of the class bool.
        The class bool is a subclass of the class int, and cannot be subclassed.

`expect(this)`
:   

    ### Methods

    `approx(self, that, rel_tol=1e-09, abs_tol=0.0)`
    :

    `called(self)`
    :

    `called_once_with(self, *args, **kwargs)`
    :

    `called_with(self, *args, **kwargs)`
    :

    `contained_in(self, that)`
    :

    `contains(self, that)`
    :

    `equals(self, expected)`
    :

    `greater_than(self, that)`
    :

    `greater_than_or_equals(self, that)`
    :

    `has_calls(self, calls, any_order=False)`
    :

    `has_length(self, length)`
    :

    `identical_to(self, that)`
    :

    `instance_of(self, type)`
    :

    `less_than(self, that)`
    :

    `less_than_or_equals(self, that)`
    :

    `not_approx(self, that, rel_tol=1e-09, abs_tol=0.0)`
    :

    `not_called(self)`
    :

    `not_contained_in(self, that)`
    :

    `not_contains(self, that)`
    :

    `not_equals(self, that)`
    :

    `not_greater_than(self, that)`
    :

    `not_greater_than_or_equals(self, that)`
    :

    `not_has_length(self, length)`
    :

    `not_identical_to(self, that)`
    :

    `not_instance_of(self, type)`
    :

    `not_less_than(self, that)`
    :

    `not_less_than_or_equals(self, that)`
    :

    `not_satisfies(self, predicate)`
    :

    `satisfies(self, predicate)`
    :

`raises(expected_ex_type)`
: