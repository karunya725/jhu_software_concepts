"""Package configuration for the Module 5 Grad Cafe Analysis App."""

from setuptools import find_packages, setup

setup(
    name="grad-cafe-analysis-app",
    version="1.0.0",
    description="Flask and PostgreSQL Grad Cafe analysis application.",
    author="Karunya Narayanamurthy",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    py_modules=["app", "db_utils", "load_data", "query_data"],
    install_requires=[
        "Flask",
        "psycopg[binary]",
        "beautifulsoup4",
        "python-dotenv",
    ],
)