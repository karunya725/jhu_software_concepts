Architecture
============

The application follows a simple Flask application architecture with a PostgreSQL database backend.

Application Layer
-----------------

The Flask application is defined in ``src/app.py``. It creates the web application, defines routes, connects to the database, builds filter clauses, and renders the analysis page.

The main routes are:

* ``/`` - redirects to the analysis page.
* ``/analysis`` - displays the analysis dashboard.
* ``/pull-data`` - starts the incremental data pull pipeline.
* ``/update-analysis`` - refreshes the analysis using the current database.

Database Layer
--------------

The application uses PostgreSQL to store applicant records.

The required applicant table includes fields such as:

* ``p_id``
* ``program``
* ``comments``
* ``date_added``
* ``url``
* ``status``
* ``term``
* ``us_or_international``
* ``gpa``
* ``gre``
* ``gre_v``
* ``gre_aw``
* ``degree``
* ``llm_generated_program``
* ``llm_generated_university``

The ``db_utils.py`` file contains helper functions used by the test suite to create, clear, insert into, and query the test database.

Data Loading Layer
------------------

The ``load_data.py`` file handles loading cleaned applicant records from JSON data into PostgreSQL. It also includes helper functions for cleaning numeric values, dates, and admission status labels.

Query Layer
-----------

The ``query_data.py`` file contains database connection and query helper functions. These helpers make it easier to separate SQL access from application and testing logic.

Testing Architecture
--------------------

The test suite is organized as stated below:

* Web page tests
* Button behavior tests
* Analysis formatting tests
* Database schema and insert tests
* Duplicate/idempotency tests
* Integration tests

The tests use Pytest fixtures, monkeypatching, and fake data so that the test suite does not depend on live Grad Café scraping or LLM processing.