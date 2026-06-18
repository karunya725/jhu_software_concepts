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