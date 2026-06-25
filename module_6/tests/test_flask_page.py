import pytest
from bs4 import BeautifulSoup


@pytest.mark.web
def test_analysis_page_loads(client):
    response = client.get("/analysis")

    assert response.status_code == 200


@pytest.mark.web
def test_analysis_page_contains_required_text(client):
    response = client.get("/analysis")
    html = response.data.decode("utf-8")

    assert "Analysis" in html
    assert "Pull Data" in html
    assert "Update Analysis" in html
    assert "Answer:" in html


@pytest.mark.web
def test_analysis_page_contains_required_buttons(client):
    response = client.get("/analysis")
    soup = BeautifulSoup(response.data, "html.parser")

    pull_button = soup.find(attrs={"data-testid": "pull-data-btn"})
    update_button = soup.find(attrs={"data-testid": "update-analysis-btn"})

    assert pull_button is not None
    assert update_button is not None

@pytest.mark.web
def test_home_redirects_to_analysis(client):
    response = client.get("/")

    assert response.status_code == 302
    assert "/analysis" in response.headers["Location"]

@pytest.mark.web
def test_analysis_endpoint_handles_malicious_filter_without_crashing(client):
    response = client.get(
        "/analysis",
        query_string={
            "term": "Fall 2026' OR '1'='1",
            "degree": "Masters",
            "status": "Accepted",
            "applicant_type": "International",
            "university": "Johns Hopkins University'; DROP TABLE applicants; --",
        },
    )

    assert response.status_code == 200
    assert b"Analysis" in response.data
    assert b"Answer:" in response.data


@pytest.mark.web
def test_analysis_endpoint_does_not_expose_sql_error_for_malicious_input(client):
    response = client.get(
        "/analysis",
        query_string={
            "university": "'; SELECT * FROM applicants; --",
        },
    )

    html = response.data.decode("utf-8", errors="ignore").lower()

    assert response.status_code == 200
    assert "syntax error" not in html
    assert "traceback" not in html
    assert "psycopg" not in html