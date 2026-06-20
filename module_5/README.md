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

