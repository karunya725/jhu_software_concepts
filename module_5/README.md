Name: Karunya, knaraya7

Module Info: Module 5 - Software Assurance + Secure SQL
Due Date: 22 Jun 2026, 11:59PM

GitHub SSH URL:
git@github.com:karunya725/jhu_software_concepts.git

## Overview

In this module, I focused on software assurance and secure SQL practices. I updated the project to use Pylint, safer database credentials, psycopg SQL composition, parameterized queries, LIMIT enforcement, least-privilege database access, dependency analysis, Snyk scans, and GitHub Actions CI.

## Important Security Notes

Real database credentials are not stored in the code or committed to GitHub. The project reads database settings from environment variables. A `.env.example` file is included only as a template, and the real `.env` file is ignored by Git.

The app was tested with a least-privilege PostgreSQL user named `gradcafe_app_user`. This user is not a superuser and was granted only the permissions needed for the Flask analysis dashboard to read from the `applicants` table.

## Fresh Install Instructions

These commands should be run from inside the `module_5` folder.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
py -m pip install -e .
```

For tests, I used the test database:

```powershell
$env:DATABASE_URL="postgresql://postgres:your_encoded_password@localhost:5432/gradcafe_test_db"
```

For the real Flask app, I use the least-privilege app user:

```powershell
$env:DATABASE_URL="postgresql://gradcafe_app_user:your_encoded_password@localhost:5432/gradcafe_db"
```

## Database Setup

The tests use `gradcafe_test_db`. The real application uses `gradcafe_db`.

To create the test database:

```powershell
createdb -U postgres gradcafe_test_db
```

To create the real application database:

```powershell
createdb -U postgres gradcafe_db
```

To load the real applicant data:

```powershell
cd src
py load_data.py
```

The data file expected by `load_data.py` is:

```text
src/data/llm_extend_applicant_data.json
```

## Least-Privilege Database User

The Flask dashboard was tested using a limited PostgreSQL user:

```sql
CREATE USER gradcafe_app_user WITH PASSWORD 'replace_with_secure_password';
GRANT CONNECT ON DATABASE gradcafe_db TO gradcafe_app_user;
GRANT USAGE ON SCHEMA public TO gradcafe_app_user;
GRANT SELECT ON TABLE applicants TO gradcafe_app_user;
```

This user does not have superuser access and was not granted DROP, ALTER, CREATE, or owner-level permissions.

## Running the Flask App

From inside `module_5/src`:

```powershell
py app.py
```

Then open:

```text
http://127.0.0.1:5000/analysis
```

## Running Tests

From inside `module_5`:

```powershell
py -m pytest
```

To run tests without coverage while developing:

```powershell
py -m pytest --no-cov
```

The project is configured to require 100% coverage through `pytest.ini`.

## Pylint

Pylint is run only on the Python files inside `module_5/src`:

```powershell
py -m pylint --rcfile=.pylintrc --fail-under=10 src
```

At the time of submission, Pylint passes with:

```text
Your code has been rated at 10.00/10
```

## SQL Injection Defenses

The SQL refactor focused on keeping SQL structure separate from user-supplied values. Filter values from the Flask dashboard are passed through parameterized query values instead of being inserted directly into SQL text.

Dynamic SQL components are handled with `psycopg.sql.SQL` and `sql.Identifier`. User values are passed through `%s` placeholders and parameter lists. Queries also include LIMIT clauses, and helper logic clamps limits to a safe range.

I also added endpoint-level malicious input tests for `/analysis` to make sure SQL-like input does not crash the page or expose SQL error messages.

## Dependency Graph

The dependency graph was generated with pydeps and Graphviz:

```powershell
pydeps src --noshow -o dependency.svg
```

The output is saved as:

```text
dependency.svg
```

## Snyk Security Scans

Snyk dependency scanning was run with:

```powershell
snyk test
```

The screenshot is saved as:

```text
snyk-analysis.png
```

Snyk identified one high-severity transitive dependency issue in `diskcache`, introduced through `llama-cpp-python`. Snyk reported that no direct upgrade or patch was available, so I documented it as an accepted risk and kept the dependency because the local LLM pipeline depends on it.

I also ran:

```powershell
snyk code test
```

The screenshot is saved as:

```text
snyk-code-analysis.png
```

The Snyk Code scan found low-severity path traversal findings in the local LLM helper script and a debug-mode finding in the Flask app. The debug-mode issue was fixed by making debug mode controlled by the `FLASK_DEBUG` environment variable instead of hard-coding `debug=True`.

## GitHub Actions

The Module 5 CI workflow is located at:

```text
.github/workflows/module5_ci.yml
```

The workflow runs:

- Pylint with `--fail-under=10`
- pydeps dependency graph generation and validation
- Pytest with coverage
- Snyk dependency scanning

The successful GitHub Actions screenshot is included as:

```text
actions_success.png
```