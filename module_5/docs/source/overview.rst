Overview
========

This project is a Flask and PostgreSQL web application that analyzes graduate admissions data from Grad Café.

The application was originally built for Module 3 and was refactored in Module 4 to improve its structure, testing, documentation, and deployment workflow. The app now separates source code into the ``src`` folder, tests into the ``tests`` folder, and documentation into the ``docs`` folder.

Main Features
-------------

* Displays analysis of graduate admissions records.
* Uses PostgreSQL as the main database.
* Provides filterable dashboard results.
* Supports a Pull Data button for incremental updates.
* Supports an Update Analysis button for refreshing analysis results.
* Uses Pytest for automated testing.
* Uses GitHub Actions for continuous integration.
* Uses Sphinx for project documentation.

Project Structure
-----------------

The main Module 4 structure is:

.. code-block:: text

   module_4/
   ├── src/
   │   ├── app.py
   │   ├── db_utils.py
   │   ├── load_data.py
   │   └── query_data.py
   ├── tests/
   ├── docs/
   ├── pytest.ini
   ├── requirements.txt
   ├── coverage_summary.txt
   └── README.md