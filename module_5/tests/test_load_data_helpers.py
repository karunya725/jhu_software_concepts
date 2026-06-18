import json

import pytest

import load_data


class FakeCursor:
    """
    Fake database cursor for testing load_data helper functions.
    """

    def __init__(self):
        self.executed_queries = []
        self.executed_params = []

    def execute(self, query, params=None):
        self.executed_queries.append(query)
        self.executed_params.append(params)


def make_fake_load_record(record_id=900001):
    """
    Creates a fake record using the exact key names expected by load_data.insert_records().
    """
    return {
        "gradcafe_id": record_id,
        "program": "Computer Science",
        "comments": "Fake record.",
        "date_added": "2026-06-15",
        "url": f"https://example.com/test-record-{record_id}",
        "status": "Accepted",
        "term": "Fall 2026",
        "US/International": "International",
        "GPA": 3.8,
        "Degree": "Masters",
        "llm-generated-program": "Computer Science",
        "llm-generated-university": "Johns Hopkins University",
        "raw_record": {
            "id": record_id,
            "greq": 168.0,
            "grev": 160.0,
            "grew": 4.5,
        },
    }


@pytest.mark.db
def test_create_table_executes_create_table_sql():
    cursor = FakeCursor()

    load_data.create_table(cursor)

    executed_sql = " ".join(cursor.executed_queries)

    assert "DROP TABLE IF EXISTS applicants" in executed_sql
    assert "CREATE TABLE applicants" in executed_sql
    assert "p_id INTEGER PRIMARY KEY" in executed_sql
    assert "llm_generated_university TEXT" in executed_sql


@pytest.mark.db
def test_load_json_data_reads_records_from_file(tmp_path, monkeypatch):
    fake_data_file = tmp_path / "fake_applicant_data.json"
    fake_records = [
        {
            "id": 1,
            "Program": "Computer Science",
            "Status": "Accepted",
        }
    ]

    fake_data_file.write_text(json.dumps(fake_records), encoding="utf-8")

    monkeypatch.setattr(load_data, "DATA_FILE", fake_data_file)

    records = load_data.load_json_data()

    assert records == fake_records


@pytest.mark.db
def test_insert_records_inserts_valid_record():
    cursor = FakeCursor()
    records = [make_fake_load_record()]

    inserted_count = load_data.insert_records(cursor, records)

    assert inserted_count == 1
    assert len(cursor.executed_queries) == 1
    assert "INSERT INTO applicants" in cursor.executed_queries[0]


@pytest.mark.db
def test_insert_records_maps_raw_gre_fields_correctly():
    cursor = FakeCursor()
    records = [make_fake_load_record()]

    load_data.insert_records(cursor, records)

    inserted_row = cursor.executed_params[0]

    assert inserted_row[9] == 168.0
    assert inserted_row[10] == 160.0
    assert inserted_row[11] == 4.5


@pytest.mark.db
def test_insert_records_handles_missing_raw_record():
    cursor = FakeCursor()

    record = make_fake_load_record(record_id=900002)
    record.pop("raw_record")

    load_data.insert_records(cursor, [record])

    inserted_row = cursor.executed_params[0]

    assert inserted_row[9] is None
    assert inserted_row[10] is None
    assert inserted_row[11] is None


@pytest.mark.db
def test_insert_records_skips_record_without_id():
    cursor = FakeCursor()

    record = make_fake_load_record()
    record.pop("gradcafe_id")
    record["raw_record"].pop("id")

    inserted_count = load_data.insert_records(cursor, [record])

    assert inserted_count == 0
    assert cursor.executed_queries == []

@pytest.mark.db
def test_clean_float_handles_empty_string():
    assert load_data.clean_float("") is None


@pytest.mark.db
def test_clean_float_handles_non_numeric_string():
    assert load_data.clean_float("not available") is None


@pytest.mark.db
def test_clean_date_handles_none():
    assert load_data.clean_date(None) is None


@pytest.mark.db
def test_clean_date_parses_valid_date():
    assert str(load_data.clean_date("Added on May 29, 2026")) == "2026-05-29"


@pytest.mark.db
def test_clean_status_handles_none():
    assert load_data.clean_status(None) is None


@pytest.mark.db
@pytest.mark.parametrize(
    "raw_status, expected_status",
    [
        ("Rejected on May 29", "Rejected"),
        ("Wait listed on May 29", "Wait listed"),
        ("Interview on May 29", "Interview"),
        ("Other status", "Other status"),
    ],
)
def test_clean_status_maps_remaining_statuses(raw_status, expected_status):
    assert load_data.clean_status(raw_status) == expected_status