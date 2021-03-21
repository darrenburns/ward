Ward - A modern Python test framework
=====================================

Ward is a test framework for Python with a focus on productivity and readability. It is heavily inspired by `pytest`, but
diverges from it in several areas.

.. image:: ./_static/intro_screenshot.png
    :align: center
    :alt: An example output from Ward

Installation
------------
Run ``pip install ward``. Ward requires Python 3.6+ in order to run.

Usage
-----
You can run all tests in your current directory by just running ``ward`` with no arguments.

.. toctree::
    :maxdepth: 2
    :caption: User Guide

    guide/writing_tests
    guide/running_tests
    guide/fixtures
    guide/pyproject.toml

.. toctree::
    :maxdepth: 1
    :caption: Tutorials

    tutorials/first_tests.rst
    tutorials/testing_flask.rst