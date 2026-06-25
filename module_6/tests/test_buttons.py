import pytest

import app as app_module


class ImmediateThread:
    """
    Fake thread used for tests.

    Instead of starting a real background thread, this immediately runs
    the target function. This prevents tests from running the real pipeline
    asynchronously.
    """

    def __init__(self, target):
        self.target = target

    def start(self):
        self.target()


@pytest.mark.buttons
def test_pull_data_returns_ok_when_not_busy(client, monkeypatch):
    called = {"pipeline": False}

    def fake_pipeline():
        called["pipeline"] = True
        app_module.PULL_DATA_RUNNING = False

    monkeypatch.setattr(app_module, "run_pull_data_pipeline", fake_pipeline)
    monkeypatch.setattr(app_module.threading, "Thread", ImmediateThread)

    app_module.PULL_DATA_RUNNING = False

    response = client.post("/pull-data")
    data = response.get_json()

    assert response.status_code == 202
    assert data["ok"] is True
    assert data["busy"] is False
    assert called["pipeline"] is True


@pytest.mark.buttons
def test_update_analysis_returns_ok_when_not_busy(client):
    app_module.PULL_DATA_RUNNING = False

    response = client.post("/update-analysis")
    data = response.get_json()

    assert response.status_code == 200
    assert data["ok"] is True
    assert data["busy"] is False


@pytest.mark.buttons
def test_update_analysis_returns_busy_when_pull_is_running(client):
    app_module.PULL_DATA_RUNNING = True

    response = client.post("/update-analysis")
    data = response.get_json()

    assert response.status_code == 409
    assert data["ok"] is False
    assert data["busy"] is True

    app_module.PULL_DATA_RUNNING = False


@pytest.mark.buttons
def test_pull_data_returns_busy_when_pull_is_running(client):
    app_module.PULL_DATA_RUNNING = True

    response = client.post("/pull-data")
    data = response.get_json()

    assert response.status_code == 409
    assert data["ok"] is False
    assert data["busy"] is True

    app_module.PULL_DATA_RUNNING = False