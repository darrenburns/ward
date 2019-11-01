---
path: "/modules/ward.fixtures"
title: "Module"
section: "modules"
---

Module ward.fixtures
====================

Functions
---------

    
`fixture(func=None, *, description=None)`
:   

Classes
-------

`CollectionError(*args, **kwargs)`
:   Common base class for all non-exit exceptions.

    ### Ancestors (in MRO)

    * ward.fixtures.TestSetupError
    * builtins.Exception
    * builtins.BaseException

`Fixture(fn)`
:   Fixture(fn: Callable)

    ### Instance variables

    `is_generator_fixture`
    :

    `key`
    :

    `name`
    :

    ### Methods

    `deps(self)`
    :

    `teardown(self)`
    :

`FixtureCache()`
:   FixtureCache(_fixtures: Dict[str, ward.fixtures.Fixture] = <factory>)

    ### Methods

    `cache_fixture(self, fixture)`
    :

    `teardown_all(self)`
    :   Run the teardown code for all generator fixtures in the cache

`FixtureExecutionError(*args, **kwargs)`
:   Common base class for all non-exit exceptions.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException

`TestSetupError(*args, **kwargs)`
:   Common base class for all non-exit exceptions.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException

    ### Descendants

    * ward.fixtures.CollectionError