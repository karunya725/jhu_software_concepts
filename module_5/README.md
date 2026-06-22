Name: Karunya

Module Info: Module 5
Due Date: 

GitHub SSH URL:
git@github.com:karunya725/jhu_software_concepts.git

## Overview
This project is a Flask + PostgreSQL web application that analyses Grad Cafe applicant data.  
It includes data ingestion, query utilities, a dashboard UI, and background pipeline execution.

## Setup Instructions

### 1. Create virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```
### 2. Install dependencies
```powershell
py -m pip install -r requirements.txt
```
### 3. Install project in editable mode
```powershell
py -m pip install -e .
```

## Running the application

From 'module_5' folder run ```py src/app.py```
Then open: http://127.0.0.1:5000/analysis

## Testing

### 1. Run tests
```powershell
py -m pytest --no-cov
```
### 2. Run with coverage
```powershell
py -m pytest
```
### 3. Run Pylint from module root'
```powershell
py -m pylint --rcfile=.pylintrc src
```

The code achieves: Your code has been rated at 10.00/10

The dependency graph shows that the Flask application depends on the Flask package and the internal src.app module. The app, query_data, and load_data modules also depend on psycopg/psycopg.sql for PostgreSQL database access and safe SQL composition. The graph shows that src.app is the main web-facing module, while src.query_data and src.load_data handle database query and loading responsibilities. db_utils does not appear prominently because it is mainly used by the test suite rather than the runtime application. Overall, the graph supports the project structure by showing a small set of focused modules connected through Flask and PostgreSQL dependencies.

Snyk identified one high-severity vulnerability in diskcache 5.6.3, introduced transitively through llama-cpp-python. The issue is categorized as deserialization of untrusted data. Snyk reported that no direct upgrade or patch is currently available. Because llama-cpp-python is required for the project’s local LLM pipeline, I did not remove the dependency. I documented the finding as an accepted risk and would mitigate it by avoiding untrusted cache inputs, keeping the dependency monitored for future patches, and limiting where the LLM pipeline is executed.

I ran the Snyk Code static analysis scan using `snyk code test`. The scan found four issues: three low-severity path traversal findings in the local LLM hosting helper script and one medium-severity debug mode finding in the main Flask application. The debug mode finding was addressed by replacing hard-coded `debug=True` with an environment-controlled `FLASK_DEBUG` setting so that debug mode is disabled by default. The path traversal findings were reviewed as local-script risks because they occur in the LLM helper script where command-line file paths are used for local input/output. I documented these findings and would further mitigate them by validating and restricting file paths to approved project directories.
