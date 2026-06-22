"""Query helper functions for Grad Cafe applicant analysis."""

import os

import psycopg
from psycopg import sql
from dotenv import load_dotenv

# -----------------------------
# Database connection settings
# -----------------------------

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")

DB_NAME = os.environ.get("DB_NAME", "gradcafe_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")


# Normalizes GPA values onto a 4.0 scale before averaging.
# Values > 2 and <= 4 are treated as already being on a 4.0 scale.
# Values > 4 and <= 5 are assumed to be on a 5.0 scale and converted to 4.0.
# Values > 5 and <= 10 are assumed to be on a 10.0 CGPA scale and converted to 4.0.
# Values <= 2, > 10, and NULL are excluded because their scale or validity is unclear.
NORMALIZED_GPA_SQL = """
    CASE
        WHEN gpa IS NULL THEN NULL
        WHEN gpa > 2 AND gpa <= 4 THEN gpa
        WHEN gpa > 4 AND gpa <= 5 THEN (gpa / 5.0) * 4.0
        WHEN gpa > 5 AND gpa <= 10 THEN (gpa / 10.0) * 4.0
        ELSE NULL
    END
"""

MAX_QUERY_LIMIT = 100
DEFAULT_QUERY_LIMIT = 50


def clamp_limit(value=None, default=DEFAULT_QUERY_LIMIT):
    """Clamp SQL LIMIT values to a safe range."""
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return default

    return max(1, min(limit, MAX_QUERY_LIMIT))


def get_connection():
    """Create and return a PostgreSQL database connection."""
    if DATABASE_URL:
        return psycopg.connect(DATABASE_URL)

    return psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )


def fetch_one(cursor, query, params=None):
    """Execute a query and return the first value from the first row."""
    cursor.execute(query, params or ())
    return cursor.fetchone()[0]


def fetch_all(cursor, query, params=None):
    """Execute a query and return all rows."""
    cursor.execute(query, params or ())
    return cursor.fetchall()


def main():  # pragma: no cover  # pylint: disable=too-many-locals
    """Query applicant records from the PostgreSQL database."""
    with get_connection() as connection:
        with connection.cursor() as cursor:

            print("\nGrad Cafe Data Analysis")
            print("=" * 50)

            q1 = fetch_one(
                cursor,
                """
                SELECT COUNT(*)
                FROM applicants
                WHERE term = 'Fall 2026'
                LIMIT 1;
                """
            )
            print(f"\n1. Fall 2026 applicant count: {q1}")

            q2 = fetch_one(
                cursor,
                """
                SELECT ROUND(
                    100.0 * SUM(
                        CASE
                            WHEN us_or_international = 'International'
                                OR COALESCE(comments, '') ILIKE '%%Canadian%%'
                                OR COALESCE(comments, '') ILIKE '%%International%%'
                            THEN 1 ELSE 0
                        END
                    )
                    /
                    SUM(
                        CASE
                            WHEN us_or_international IN (
                                'American',
                                'International',
                                'Other'
                            )
                                OR COALESCE(comments, '') ILIKE '%%Canadian%%'
                                OR COALESCE(comments, '') ILIKE '%%International%%'
                                OR COALESCE(comments, '') ILIKE '%%US Citizen%%'
                                OR COALESCE(comments, '') ILIKE '%%American%%'
                            THEN 1 ELSE 0
                        END
                    ),
                    2
                )
                FROM applicants
                LIMIT 1;
                """
            )
            print(f"2. Percent international: {q2}%")

            q3_query = sql.SQL(
                """
                SELECT
                    AVG({}) AS average_gpa,
                    AVG(
                        CASE WHEN gre BETWEEN 130 AND 170 THEN gre END
                    ) AS average_gre_quant,
                    AVG(
                        CASE WHEN gre_v BETWEEN 130 AND 170 THEN gre_v END
                    ) AS average_gre_verbal,
                    AVG(
                        CASE WHEN gre_aw BETWEEN 0.1 AND 6.0 THEN gre_aw END
                    ) AS average_gre_aw
                FROM applicants
                LIMIT 1;
                """
            ).format(sql.SQL(NORMALIZED_GPA_SQL))

            q3 = fetch_all(cursor, q3_query)[0]

            print(
                "3. Average metrics: "
                f"GPA = {round(q3[0], 2) if q3[0] is not None else None}, "
                f"GRE Quant = {round(q3[1], 2) if q3[1] is not None else None}, "
                f"GRE Verbal = {round(q3[2], 2) if q3[2] is not None else None}, "
                f"GRE AW = {round(q3[3], 2) if q3[3] is not None else None}"
            )

            q4_query = sql.SQL(
                """
                SELECT ROUND(AVG({})::numeric, 2)
                FROM applicants
                WHERE term = 'Fall 2026'
                AND (
                    us_or_international = 'American'
                    OR comments ILIKE '%%US Citizen%%'
                )
                AND {} IS NOT NULL
                LIMIT 1;
                """
            ).format(
                sql.SQL(NORMALIZED_GPA_SQL),
                sql.SQL(NORMALIZED_GPA_SQL)
            )

            q4 = fetch_one(cursor, q4_query)

            print(f"4. Average normalized GPA of American students in Fall 2026: {q4}")

            q5 = fetch_one(
                cursor,
                """
                SELECT ROUND(
                    100.0 * SUM(
                        CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END
                    ) / COUNT(*),
                    2
                )
                FROM applicants
                WHERE term = 'Fall 2026'
                LIMIT 1;
                """
            )
            print(f"5. Fall 2026 acceptance percent: {q5}%")

            q6_query = sql.SQL(
                """
                SELECT ROUND(AVG({})::numeric, 2)
                FROM applicants
                WHERE term = 'Fall 2026'
                AND status = 'Accepted'
                AND {} IS NOT NULL
                LIMIT 1;
                """
            ).format(
                sql.SQL(NORMALIZED_GPA_SQL),
                sql.SQL(NORMALIZED_GPA_SQL)
            )

            q6 = fetch_one(cursor, q6_query)

            print(f"6. Average normalized GPA of accepted Fall 2026 applicants: {q6}")

            q7 = fetch_one(
                cursor,
                """
                SELECT COUNT(*) AS jhu_masters_cs_count
                FROM applicants
                WHERE degree ILIKE '%%Master%%'
                AND llm_generated_program ILIKE '%%Computer Science%%'
                AND llm_generated_university ILIKE '%%Johns Hopkins%%'
                LIMIT 1;
                """
            )
            print(f"7. JHU Master's Computer Science count: {q7}")

            q8 = fetch_one(
                cursor,
                """
                SELECT COUNT(*)
                FROM applicants
                WHERE term ILIKE '%%2026%%'
                AND status = 'Accepted'
                AND degree ILIKE '%%PhD%%'
                AND program ILIKE '%%Computer Science%%'
                AND (
                    program ILIKE '%%Georgetown%%'
                    OR program ILIKE '%%Massachusetts Institute of Technology%%'
                    OR program ILIKE '%%MIT%%'
                    OR program ILIKE '%%Stanford%%'
                    OR program ILIKE '%%Carnegie Mellon%%'
                    OR program ILIKE '%%CMU%%'
                )
                LIMIT 1;
                """
            )
            print(
                "8. 2026 acceptances to Georgetown/MIT/Stanford/CMU "
                f"for PhD Computer Science using downloaded fields: {q8}"
            )

            q9 = fetch_one(
                cursor,
                """
                SELECT COUNT(*)
                FROM applicants
                WHERE term ILIKE '%%2026%%'
                AND status = 'Accepted'
                AND degree ILIKE '%%PhD%%'
                AND llm_generated_program ILIKE '%%Computer Science%%'
                AND (
                    llm_generated_university ILIKE '%%Georgetown%%'
                    OR llm_generated_university ILIKE
                       '%%Massachusetts Institute of Technology%%'
                    OR llm_generated_university ILIKE '%%MIT%%'
                    OR llm_generated_university ILIKE '%%Stanford%%'
                    OR llm_generated_university ILIKE '%%Carnegie Mellon%%'
                    OR llm_generated_university ILIKE '%%CMU%%'
                )
                LIMIT 1;
                """
            )
            print(
                "9. 2026 acceptances to Georgetown/MIT/Stanford/CMU "
                f"for PhD Computer Science using LLM-generated fields: {q9}"
            )

            print(
                "\n10. Which universities appear most competitive in Fall 2026 "
                "based on low acceptance rate?"
            )
            q10 = fetch_all(
                cursor,
                """
                SELECT
                    llm_generated_university,
                    COUNT(*) AS total_entries,
                    SUM(
                        CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END
                    ) AS accepted_entries,
                    ROUND(
                        100.0 * SUM(
                            CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END
                        ) / COUNT(*),
                        2
                    ) AS acceptance_rate
                FROM applicants
                WHERE term = 'Fall 2026'
                AND llm_generated_university IS NOT NULL
                GROUP BY llm_generated_university
                HAVING COUNT(*) >= 10
                ORDER BY acceptance_rate ASC, total_entries DESC
                LIMIT %s;
                """,
                (clamp_limit(10),)
            )

            for row in q10:
                print(
                    f"    {row[0]}: {row[2]} accepted out of {row[1]} "
                    f"({row[3]}% acceptance rate)"
                )

            print("\n11. Which degree type had the highest Fall 2026 acceptance rate?")
            q11 = fetch_all(
                cursor,
                """
                SELECT
                    degree,
                    COUNT(*) AS total_entries,
                    SUM(
                        CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END
                    ) AS accepted_entries,
                    ROUND(
                        100.0 * SUM(
                            CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END
                        ) / COUNT(*),
                        2
                    ) AS acceptance_rate
                FROM applicants
                WHERE term = 'Fall 2026'
                AND degree IS NOT NULL
                GROUP BY degree
                HAVING COUNT(*) >= 10
                ORDER BY acceptance_rate DESC
                LIMIT %s;
                """,
                (clamp_limit(100),)
            )

            for row in q11:
                print(
                    f"    {row[0]}: {row[2]} accepted out of {row[1]} "
                    f"({row[3]}% acceptance rate)"
                )

            print("\n" + "=" * 50)
            print("Analysis complete.\n")


if __name__ == "__main__":  # pragma: no cover
    main()
