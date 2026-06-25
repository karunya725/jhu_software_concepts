import pytest

from db_utils import (
    REQUIRED_COLUMNS,
    count_applicants,
    get_analysis_summary,
    get_schema_columns,
    insert_applicants,
)


@pytest.mark.db
def test_insert_new_applicant_row(test_db_connection, fake_applicant_record):
    inserted_count = insert_applicants(test_db_connection, [fake_applicant_record])

    assert inserted_count == 1
    assert count_applicants(test_db_connection) == 1


@pytest.mark.db
def test_required_schema_columns_exist(test_db_connection):
    schema_columns = get_schema_columns(test_db_connection)

    for column in REQUIRED_COLUMNS:
        assert column in schema_columns


@pytest.mark.db
def test_inserted_row_has_required_non_null_fields(
    test_db_connection,
    fake_applicant_record,
):
    insert_applicants(test_db_connection, [fake_applicant_record])

    with test_db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                p_id,
                program,
                date_added,
                status,
                term,
                degree,
                llm_generated_program,
                llm_generated_university
            FROM applicants
            WHERE p_id = %s;
            """,
            (fake_applicant_record["p_id"],),
        )
        row = cursor.fetchone()

    assert row is not None

    for value in row:
        assert value is not None


@pytest.mark.db
def test_duplicate_applicant_rows_are_not_inserted(
    test_db_connection,
    fake_applicant_record,
):
    first_insert_count = insert_applicants(test_db_connection, [fake_applicant_record])
    second_insert_count = insert_applicants(test_db_connection, [fake_applicant_record])

    assert first_insert_count == 1
    assert second_insert_count == 0
    assert count_applicants(test_db_connection) == 1


@pytest.mark.db
def test_analysis_summary_returns_expected_keys(
    test_db_connection,
    fake_applicant_records,
):
    insert_applicants(test_db_connection, fake_applicant_records)

    summary = get_analysis_summary(test_db_connection)

    assert set(summary.keys()) == {
        "total_applicants",
        "accepted_applicants",
        "acceptance_rate",
    }
    assert summary["total_applicants"] == 2
    assert summary["accepted_applicants"] == 1
    assert summary["acceptance_rate"] == 50.00

@pytest.mark.db
def test_analysis_summary_handles_empty_database(test_db_connection):
    summary = get_analysis_summary(test_db_connection)

    assert summary["total_applicants"] == 0
    assert summary["accepted_applicants"] == 0
    assert summary["acceptance_rate"] == 0.00

@pytest.mark.db
def test_analysis_summary_handles_empty_database(test_db_connection):
    summary = get_analysis_summary(test_db_connection)

    assert summary["total_applicants"] == 0
    assert summary["accepted_applicants"] == 0
    assert summary["acceptance_rate"] == 0.00