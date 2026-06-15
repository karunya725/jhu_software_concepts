import sys
from pathlib import Path
import os
import psycopg

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def app():
    """
    Creates a Flask test app.

    This fixture imports create_app from src/app.py and configures the app
    for testing.
    """
    from app import create_app

    test_app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
        }
    )

    return test_app


@pytest.fixture
def client(app):
    """
    Creates a Flask test client.
    """
    return app.test_client()

@pytest.fixture
def test_db_connection(monkeypatch):
    """
    Creates a connection to the test database and prepares the applicants table.
    """
    test_database_url = os.environ.get("DATABASE_URL")

    if not test_database_url:
        raise RuntimeError(
            "DATABASE_URL must be set to the test database before running DB tests."
        )

    from db_utils import create_applicants_table, clear_applicants_table

    connection = psycopg.connect(test_database_url)

    create_applicants_table(connection)
    clear_applicants_table(connection)

    yield connection

    clear_applicants_table(connection)
    connection.close()


@pytest.fixture
def fake_applicant_record():
    """
    Returns one fake applicant record using the required Module 3 schema.
    """
    return {
        "p_id": 900001,
        "program": "Computer Science",
        "comments": "Fake test applicant record.",
        "date_added": "2026-06-15",
        "url": "https://example.com/test-record-900001",
        "status": "Accepted",
        "term": "Fall 2026",
        "us_or_international": "International",
        "gpa": 3.8,
        "gre": 168.0,
        "gre_v": 160.0,
        "gre_aw": 4.5,
        "degree": "Masters",
        "llm_generated_program": "Computer Science",
        "llm_generated_university": "Johns Hopkins University",
    }


@pytest.fixture
def fake_applicant_records(fake_applicant_record):
    """
    Returns multiple fake applicant records for integration-style tests.
    """
    second_record = fake_applicant_record.copy()
    second_record.update(
        {
            "p_id": 900002,
            "url": "https://example.com/test-record-900002",
            "status": "Rejected",
            "gpa": 3.4,
            "gre": 162.0,
            "gre_v": 155.0,
            "llm_generated_university": "Stanford University",
        }
    )

    return [fake_applicant_record, second_record]