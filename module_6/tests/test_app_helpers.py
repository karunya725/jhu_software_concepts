import subprocess

import pytest

import app as app_module


@pytest.mark.db
def test_app_get_connection_uses_database_url(monkeypatch):
    monkeypatch.setattr(app_module, "DATABASE_URL", "postgresql://example-test-url")

    def fake_connect(database_url=None, **kwargs):
        return {
            "database_url": database_url,
            "settings": kwargs,
        }

    monkeypatch.setattr(app_module.psycopg, "connect", fake_connect)

    connection = app_module.get_connection()

    assert connection["database_url"] == "postgresql://example-test-url"
    assert connection["settings"] == {}


@pytest.mark.db
def test_app_get_connection_uses_local_settings_when_no_database_url(monkeypatch):
    monkeypatch.setattr(app_module, "DATABASE_URL", None)

    captured_settings = {}

    def fake_connect(**kwargs):
        captured_settings.update(kwargs)
        return "fake-local-connection"

    monkeypatch.setattr(app_module.psycopg, "connect", fake_connect)

    connection = app_module.get_connection()

    assert connection == "fake-local-connection"
    assert captured_settings["dbname"] == app_module.DB_NAME
    assert captured_settings["user"] == app_module.DB_USER
    assert captured_settings["password"] == app_module.DB_PASSWORD
    assert captured_settings["host"] == app_module.DB_HOST
    assert captured_settings["port"] == app_module.DB_PORT


@pytest.mark.analysis
def test_build_filter_where_clause_with_all_filters():
    filters = {
        "term": "Fall 2026",
        "degree": "Masters",
        "status": "Accepted",
        "applicant_type": "International",
        "university": "Johns Hopkins University",
    }

    where_sql, params = app_module.build_filter_where_clause(filters)

    where_sql_text = str(where_sql)

    assert "WHERE" in where_sql_text
    assert "term" in where_sql_text
    assert "degree" in where_sql_text
    assert "status" in where_sql_text
    assert "us_or_international" in where_sql_text
    assert "llm_generated_university" in where_sql_text

    assert params == [
        "Fall 2026",
        "Masters",
        "Accepted",
        "International",
        "Johns Hopkins University",
    ]


@pytest.mark.analysis
def test_build_filter_where_clause_with_no_filters():
    where_sql, params = app_module.build_filter_where_clause({})

    assert str(where_sql) == "SQL('')"
    assert params == []


@pytest.mark.buttons
def test_run_pull_data_pipeline_success(monkeypatch):
    calls = {}

    def fake_run(command, check, cwd):
        calls["command"] = command
        calls["check"] = check
        calls["cwd"] = cwd

    monkeypatch.setattr(app_module.subprocess, "run", fake_run)

    app_module.PULL_DATA_RUNNING = True

    app_module.run_pull_data_pipeline()

    assert calls["check"] is True
    assert calls["command"][0] == app_module.sys.executable
    assert str(calls["command"][1]) == str(app_module.PULL_DATA_SCRIPT)
    assert calls["cwd"] == app_module.BASE_DIR
    assert app_module.PULL_DATA_RUNNING is False


@pytest.mark.buttons
def test_run_pull_data_pipeline_handles_subprocess_error(monkeypatch):
    def fake_run(command, check, cwd):
        raise subprocess.CalledProcessError(returncode=1, cmd=command)

    monkeypatch.setattr(app_module.subprocess, "run", fake_run)

    app_module.PULL_DATA_RUNNING = True

    app_module.run_pull_data_pipeline()

    assert app_module.PULL_DATA_RUNNING is False

@pytest.mark.analysis
def test_clamp_limit_returns_default_for_invalid_value():
    assert app_module.clamp_limit("not-a-number") == app_module.DEFAULT_QUERY_LIMIT


@pytest.mark.analysis
def test_clamp_limit_clamps_large_value_to_maximum():
    assert app_module.clamp_limit(1000) == app_module.MAX_QUERY_LIMIT


@pytest.mark.analysis
def test_clamp_limit_clamps_small_value_to_minimum():
    assert app_module.clamp_limit(0) == 1


@pytest.mark.analysis
def test_get_condition_joiner_without_filters():
    joiner = app_module.get_condition_joiner(False)

    assert str(joiner) == "SQL('WHERE')"


@pytest.mark.analysis
def test_get_condition_joiner_with_filters():
    joiner = app_module.get_condition_joiner(True)

    assert str(joiner) == "SQL('AND')"