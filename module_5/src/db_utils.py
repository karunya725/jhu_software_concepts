"""
Database utility functions for testing and inserting Grad Café applicant records.
"""

REQUIRED_COLUMNS = [
    "p_id",
    "program",
    "comments",
    "date_added",
    "url",
    "status",
    "term",
    "us_or_international",
    "gpa",
    "gre",
    "gre_v",
    "gre_aw",
    "degree",
    "llm_generated_program",
    "llm_generated_university",
]


def create_applicants_table(connection):
    """
    Creates the applicants table using the required Module 3 schema.

    :param connection: Active psycopg database connection.
    :return: None.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS applicants (
                p_id INTEGER PRIMARY KEY,
                program TEXT,
                comments TEXT,
                date_added DATE,
                url TEXT,
                status TEXT,
                term TEXT,
                us_or_international TEXT,
                gpa FLOAT,
                gre FLOAT,
                gre_v FLOAT,
                gre_aw FLOAT,
                degree TEXT,
                llm_generated_program TEXT,
                llm_generated_university TEXT
            );
            """
        )
    connection.commit()


def clear_applicants_table(connection):
    """
    Removes all rows from the applicants table.

    :param connection: Active psycopg database connection.
    :return: None.
    """
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM applicants;")
    connection.commit()


def insert_applicants(connection, records):
    """
    Inserts applicant records into the applicants table.

    Duplicate p_id values are ignored so repeated pulls do not create duplicates.

    :param connection: Active psycopg database connection.
    :param records: List of applicant dictionaries.
    :return: Number of rows actually inserted.
    """
    inserted_count = 0

    with connection.cursor() as cursor:
        for record in records:
            cursor.execute(
                """
                INSERT INTO applicants (
                    p_id,
                    program,
                    comments,
                    date_added,
                    url,
                    status,
                    term,
                    us_or_international,
                    gpa,
                    gre,
                    gre_v,
                    gre_aw,
                    degree,
                    llm_generated_program,
                    llm_generated_university
                )
                VALUES (
                    %(p_id)s,
                    %(program)s,
                    %(comments)s,
                    %(date_added)s,
                    %(url)s,
                    %(status)s,
                    %(term)s,
                    %(us_or_international)s,
                    %(gpa)s,
                    %(gre)s,
                    %(gre_v)s,
                    %(gre_aw)s,
                    %(degree)s,
                    %(llm_generated_program)s,
                    %(llm_generated_university)s
                )
                ON CONFLICT (p_id) DO NOTHING;
                """,
                record,
            )

            inserted_count += cursor.rowcount

    connection.commit()
    return inserted_count


def count_applicants(connection):
    """
    Counts rows in the applicants table.

    :param connection: Active psycopg database connection.
    :return: Number of applicant rows.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM applicants;")
        return cursor.fetchone()[0]


def get_schema_columns(connection):
    """
    Returns column names for the applicants table.

    :param connection: Active psycopg database connection.
    :return: List of column names.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'applicants'
            ORDER BY ordinal_position;
            """
        )
        return [row[0] for row in cursor.fetchall()]


def get_analysis_summary(connection):
    """
    Returns a small analysis summary dictionary used for tests.

    :param connection: Active psycopg database connection.
    :return: Dictionary with expected analysis keys.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM applicants;")
        total_applicants = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM applicants
            WHERE status = 'Accepted';
            """
        )
        accepted_applicants = cursor.fetchone()[0]

        if total_applicants == 0:
            acceptance_rate = 0.00
        else:
            acceptance_rate = round((accepted_applicants / total_applicants) * 100, 2)

    return {
        "total_applicants": total_applicants,
        "accepted_applicants": accepted_applicants,
        "acceptance_rate": acceptance_rate,
    }
