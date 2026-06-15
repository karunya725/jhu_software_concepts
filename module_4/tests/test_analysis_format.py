import re
import pytest
from bs4 import BeautifulSoup
from db_utils import insert_applicants


@pytest.mark.analysis
def test_analysis_page_has_answer_labels(client):
    response = client.get("/analysis")
    html = response.data.decode("utf-8")

    assert response.status_code == 200
    assert "Answer:" in html


@pytest.mark.analysis
def test_analysis_page_has_multiple_answer_labels(client):
    response = client.get("/analysis")
    soup = BeautifulSoup(response.data, "html.parser")

    answer_text_count = soup.get_text().count("Answer:")

    assert answer_text_count >= 5


@pytest.mark.analysis
def test_percentages_are_formatted_with_two_decimals(
    client,
    test_db_connection,
    fake_applicant_records,
):
    insert_applicants(test_db_connection, fake_applicant_records)

    response = client.get("/analysis")
    html = response.data.decode("utf-8")

    percentage_matches = re.findall(r"\d+\.\d{2}%", html)

    assert percentage_matches

    for percentage in percentage_matches:
        assert re.fullmatch(r"\d+\.\d{2}%", percentage)