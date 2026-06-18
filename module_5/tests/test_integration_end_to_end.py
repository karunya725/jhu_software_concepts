import re

import pytest

import app as app_module
from db_utils import count_applicants, insert_applicants


class ImmediateThread:
    """
    Fake thread for integration tests.

    Instead of running the pull pipeline in the background, it runs immediately.
    This keeps the test deterministic and avoids arbitrary sleep().
    """

    def __init__(self, target):
        self.target = target

    def start(self):
        self.target()


@pytest.mark.integration
def test_pull_update_render_end_to_end(
    client,
    test_db_connection,
    fake_applicant_records,
    monkeypatch,
):
    """
    Given fake applicant records,
    when Pull Data and Update Analysis are triggered,
    then rows are inserted and the analysis page renders updated results.
    """

    def fake_pull_pipeline():
        insert_applicants(test_db_connection, fake_applicant_records)
        app_module.PULL_DATA_RUNNING = False

    monkeypatch.setattr(app_module, "run_pull_data_pipeline", fake_pull_pipeline)
    monkeypatch.setattr(app_module.threading, "Thread", ImmediateThread)

    app_module.PULL_DATA_RUNNING = False

    pull_response = client.post("/pull-data")
    pull_data = pull_response.get_json()

    assert pull_response.status_code == 202
    assert pull_data["ok"] is True
    assert count_applicants(test_db_connection) == 2

    update_response = client.post("/update-analysis")
    update_data = update_response.get_json()

    assert update_response.status_code == 200
    assert update_data["ok"] is True

    page_response = client.get("/analysis")
    html = page_response.data.decode("utf-8")

    assert page_response.status_code == 200
    assert "Analysis" in html
    assert "Answer:" in html

    percentage_matches = re.findall(r"\d+\.\d{2}%", html)
    assert percentage_matches


@pytest.mark.integration
def test_multiple_pulls_with_overlapping_data_do_not_duplicate_rows(
    client,
    test_db_connection,
    fake_applicant_records,
    monkeypatch,
):
    """
    Given the same fake records are pulled twice,
    when Pull Data is triggered twice,
    then duplicate rows are not inserted.
    """

    def fake_pull_pipeline():
        insert_applicants(test_db_connection, fake_applicant_records)
        app_module.PULL_DATA_RUNNING = False

    monkeypatch.setattr(app_module, "run_pull_data_pipeline", fake_pull_pipeline)
    monkeypatch.setattr(app_module.threading, "Thread", ImmediateThread)

    app_module.PULL_DATA_RUNNING = False

    first_response = client.post("/pull-data")
    first_data = first_response.get_json()

    assert first_response.status_code == 202
    assert first_data["ok"] is True
    assert count_applicants(test_db_connection) == 2

    second_response = client.post("/pull-data")
    second_data = second_response.get_json()

    assert second_response.status_code == 202
    assert second_data["ok"] is True
    assert count_applicants(test_db_connection) == 2