import pytest
import query_data


class FakeCursor:
    def __init__(self):
        self.executed_query = None
        self.executed_params = None

    def execute(self, query, params=()):
        self.executed_query = query
        self.executed_params = params

    def fetchone(self):
        return [42]

    def fetchall(self):
        return [("row1",), ("row2",)]


@pytest.mark.db
def test_query_data_fetch_one_returns_first_value():
    cursor = FakeCursor()

    result = query_data.fetch_one(cursor, "SELECT 42;")

    assert result == 42
    assert cursor.executed_query == "SELECT 42;"
    assert cursor.executed_params == ()


@pytest.mark.db
def test_query_data_fetch_one_uses_params():
    cursor = FakeCursor()

    result = query_data.fetch_one(cursor, "SELECT %s;", (42,))

    assert result == 42
    assert cursor.executed_params == (42,)


@pytest.mark.db
def test_query_data_fetch_all_returns_all_rows():
    cursor = FakeCursor()

    result = query_data.fetch_all(cursor, "SELECT * FROM applicants;")

    assert result == [("row1",), ("row2",)]
    assert cursor.executed_query == "SELECT * FROM applicants;"


@pytest.mark.db
def test_query_data_normalized_gpa_sql_contains_expected_cases():
    sql = query_data.NORMALIZED_GPA_SQL

    assert "WHEN gpa IS NULL THEN NULL" in sql
    assert "WHEN gpa > 2 AND gpa <= 4 THEN gpa" in sql
    assert "WHEN gpa > 4 AND gpa <= 5" in sql
    assert "WHEN gpa > 5 AND gpa <= 10" in sql

@pytest.mark.db
def test_query_data_get_connection_uses_database_settings(monkeypatch):
    captured_settings = {}

    def fake_connect(**kwargs):
        captured_settings.update(kwargs)
        return "fake connection"

    monkeypatch.setattr(query_data, "DATABASE_URL", None)
    monkeypatch.setattr(query_data.psycopg, "connect", fake_connect)

    connection = query_data.get_connection()

    assert connection == "fake connection"
    assert captured_settings["dbname"] == query_data.DB_NAME
    assert captured_settings["user"] == query_data.DB_USER
    assert captured_settings["password"] == query_data.DB_PASSWORD
    assert captured_settings["host"] == query_data.DB_HOST
    assert captured_settings["port"] == query_data.DB_PORT

@pytest.mark.db
def test_query_data_get_connection_uses_database_url(monkeypatch):
    captured_args = {}

    def fake_connect(database_url):
        captured_args["database_url"] = database_url
        return "fake url connection"

    monkeypatch.setattr(
        query_data,
        "DATABASE_URL",
        "postgresql://postgres:test@localhost:5432/gradcafe_test_db"
    )
    monkeypatch.setattr(query_data.psycopg, "connect", fake_connect)

    connection = query_data.get_connection()

    assert connection == "fake url connection"
    assert (
        captured_args["database_url"]
        == "postgresql://postgres:test@localhost:5432/gradcafe_test_db"
    )

@pytest.mark.db
def test_query_data_clamp_limit_returns_default_for_invalid_value():
    assert query_data.clamp_limit("not-a-number") == query_data.DEFAULT_QUERY_LIMIT


@pytest.mark.db
def test_query_data_clamp_limit_clamps_large_value_to_maximum():
    assert query_data.clamp_limit(1000) == query_data.MAX_QUERY_LIMIT


@pytest.mark.db
def test_query_data_clamp_limit_clamps_small_value_to_minimum():
    assert query_data.clamp_limit(0) == 1


@pytest.mark.db
def test_query_data_clamp_limit_accepts_valid_value():
    assert query_data.clamp_limit(25) == 25