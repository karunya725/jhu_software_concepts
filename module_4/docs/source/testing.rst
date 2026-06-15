Testing Guide
=============

This project uses Pytest for automated testing and pytest-cov for coverage reporting.

Test Categories
---------------

All tests are marked with one of the following markers:

* ``web``
* ``buttons``
* ``analysis``
* ``db``
* ``integration``

These markers are defined in ``pytest.ini``.

Running the Full Test Suite
---------------------------

From inside the ``module_4`` folder, run:

.. code-block:: powershell

   py -m pytest

Running Tests Without Coverage
------------------------------

During development, tests can be run without coverage using:

.. code-block:: powershell

   py -m pytest --no-cov

Running Tests by Marker
-----------------------

The full marked test suite can be run with:

.. code-block:: powershell

   py -m pytest -m "web or buttons or analysis or db or integration"

Coverage
--------

The project is configured to require 100% test coverage.

Coverage settings are stored in ``pytest.ini``:

.. code-block:: ini

   [pytest]
   addopts = -q --cov=src --cov-report=term-missing --cov-fail-under=100

The saved coverage output is included in:

.. code-block:: text

   module_4/coverage_summary.txt

Testing Strategy
----------------

The test suite avoids live scraping, long-running LLM calls, and manual UI interaction. Instead, it uses:

* Fake applicant records
* Test database fixtures
* Monkeypatched background pipeline functions
* Fake thread objects
* Isolated PostgreSQL test database setup

This keeps the tests repeatable and suitable for GitHub Actions.