Name: Karunya

Module Info: Module 4 - Pytest and Sphinx
Due Date: 15 Jun 2026, 11:59PM

GitHub SSH URL:
git@github.com:karunya725/jhu_software_concepts.git

## Documentation

The published Sphinx documentation is available here:

[Read the Docs Documentation](https://grad-cafe-analysis-app.readthedocs.io/en/latest/)

## Overview

Module 4 is a continuation of Grad Café analysis application. The original Module 3 project was refactored into a cleaner structure with separate folders for source code, tests, and documentation.

The application uses Flask and PostgreSQL to analyze graduate admissions data. It includes an analysis dashboard, filterable results, a Pull Data button for incremental data updates, and an Update Analysis button for refreshing the analysis page.

For Module 4, I added automated Pytest tests, 100% test coverage, GitHub Actions continuous integration, and Sphinx documentation published through Read the Docs.

## Setup Instructions

From inside the module_4 folder, install the required packages: py -m pip install -r requirements.txt

The application uses PostgreSQL. For local development, the database connection can be configured through the `DATABASE_URL` environment variable.

Example: $env:DATABASE_URL="postgresql://postgres:your_password@localhost:5432/gradcafe_test_db"

## Running the Flask App

1. From inside the module_4/src folder, run: py app.py

2. Then open the local Flask URL shown in the terminal.

## Running Tests

From inside the module_4 folder, run the full test suite: py -m pytest

To run tests without coverage during development: py -m pytest --no-cov

To run the required marked test suite: py -m pytest -m "web or buttons or analysis or db or integration"

## Test Markers

The Pytest suite uses the following required markers:
- web
- buttons
- analysis
- db
- integration

These markers are defined in pytest.ini.

## Coverage

The project is configured to require 100% test coverage using pytest-cov.

The coverage settings are in pytest.ini:

```ini
[pytest]
addopts = -q --cov=src --cov-report=term-missing --cov-fail-under=100
```

The saved coverage output is included in: module_4/coverage_summary.txt

At the time of submission, the test suite passes with:
- 45 passed
- 100% coverage

## GitHub Actions

GitHub Actions is configured to run the Pytest suite automatically with a PostgreSQL service.

The workflow file is located at: module_4/.github/workflows/tests.yml

A copy is also included at the repository root so that GitHub can detect and run the workflow: .github/workflows/tests.yml

The successful GitHub Actions run screenshot is included as: module_4/actions_success.png

## Sphinx Documentation

Sphinx documentation is located in: module_4/docs/

The documentation includes:
- overview
- architecture
- api reference
- testing guide

To build the documentation locally, run this from inside module_4: py -m sphinx -b html docs/source docs/build/html

The generated local HTML documentation can be opened from: module_4/docs/build/html/index.html
