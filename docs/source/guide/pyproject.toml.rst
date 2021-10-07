.. _pyproject:

Configuration
=============

How does Ward use ``pyproject.toml``?
-------------------------------------

You can configure Ward using the standard ``pyproject.toml`` configuration file, defined in PEP 518.

You don't need a ``pyproject.toml`` file to use Ward.

If you do decide to use one, Ward will find and read your ``pyproject.toml`` file, and treat the values inside it as defaults.

If you pass an option via the command line that also appears in your ``pyproject.toml``, the option supplied via the command line takes priority.

Where does Ward look for ``pyproject.toml``?
--------------------------------------------

The algorithm Ward uses to discover your ``pyproject.toml`` is described at a high level below.

1. Find the common base directory of all files passed in via the ``--path`` option (default to the current working directory).
2. Starting from this directory, look at all parent directories, and return the file if it is found.
3. If a directory contains a ``.git`` directory/file, a .hg directory, or the ``pyproject.toml`` file, stop searching.

This is the same process Black (the popular code formatting tool) uses to discover the file.

Example ``pyproject.toml`` config file
--------------------------------------

The ``pyproject.toml`` file contains different sections for different tools. Ward uses the ``[tool.ward]`` section, so
all of your Ward configuration should appear there:

.. code-block:: toml

    [tool.ward]
    path = ["unit_tests", "integration_tests"]  # supply multiple paths using a list
    capture-output = false  # enable or disable output capturing (e.g. to use debugger)
    order = "standard"  # or 'random'
    test-output-style = "test-per-line"  # or 'dots-global', 'dot-module'
    fail-limit = 20  # stop the run if 20 fails occur
    search = "my_function"  # search in test body or description
    progress-style = ["bar"]  # display a progress bar during the run
