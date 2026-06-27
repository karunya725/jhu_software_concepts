"""Flask application for displaying Grad Cafe analysis results."""

import os
from pathlib import Path
import subprocess
import sys
import threading

import psycopg
from psycopg import sql
from flask import Flask, jsonify, redirect, render_template, request, url_for
from dotenv import load_dotenv
from publisher import publish_task

load_dotenv()

PULL_DATA_RUNNING = False
PULL_DATA_LOCK = threading.Lock()


def create_app(test_config=None):
    """Create and configure the Flask application."""

    flask_app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    flask_app.config.from_mapping(
        SECRET_KEY="dev",
        TESTING=False,
    )

    if test_config is not None:
        flask_app.config.update(test_config)

    @flask_app.route("/")
    def home():
        """Redirect the home page to the analysis dashboard."""
        return redirect(url_for("analysis"))

    @flask_app.route("/analysis")
    def analysis():
        """Render the analysis dashboard page."""
        filters = {
            "term": request.args.get("term", ""),
            "degree": request.args.get("degree", ""),
            "status": request.args.get("status", ""),
            "applicant_type": request.args.get("applicant_type", ""),
            "university": request.args.get("university", ""),
        }

        results = get_analysis_results()
        filter_options = get_filter_options()
        dashboard = get_dashboard_results(filters)

        return render_template(
            "index.html",
            results=results,
            filters=filters,
            filter_options=filter_options,
            dashboard=dashboard,
            pull_data_running=PULL_DATA_RUNNING
        )

    @flask_app.route("/pull-data", methods=["POST"])
    def pull_data():
        """
        Start the incremental data pull pipeline.

        Returns JSON so tests and the webpage can check whether the pull started.
        """
        global PULL_DATA_RUNNING  # pylint: disable=global-statement

        with PULL_DATA_LOCK:
            if PULL_DATA_RUNNING:
                return jsonify({
                    "ok": False,
                    "busy": True,
                    "message": (
                        "Pull Data is already running. "
                        "Please wait before starting another request."
                    )
                }), 409

            PULL_DATA_RUNNING = True

        task = publish_task(
            kind="pull_data",
            payload={
                "source": "web",
                "action": "load_seed_or_incremental_data",
            },
        )

        with PULL_DATA_LOCK:
            PULL_DATA_RUNNING = False

        return jsonify({
            "ok": True,
            "busy": False,
            "task_id": task["task_id"],
            "message": (
                "Pull Data task has been queued. "
                "The worker will process it in the background."
            )
        }), 202

    @flask_app.route("/update-analysis", methods=["POST"])
    def update_analysis():
        """
        Refresh analysis unless Pull Data is currently running.

        Returns JSON so tests and the webpage can check the update status.
        """
        if PULL_DATA_RUNNING:
            return jsonify({
                "ok": False,
                "busy": True,
                "message": (
                    "Analysis cannot be updated while Pull Data is running. "
                    "Please wait and try again."
                )
            }), 409

        task = publish_task(
            kind="update_analysis",
            payload={
                "source": "web",
                "action": "refresh_analysis",
            },
        )

        return jsonify({
            "ok": True,
            "busy": False,
            "task_id": task["task_id"],
            "message": "Update Analysis task has been queued."
        }), 202

    return flask_app


# ------------------------------
# Database connection settings
# ------------------------------

DATABASE_URL = os.environ.get("DATABASE_URL")

DB_NAME = os.environ.get("DB_NAME", "gradcafe_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")


def get_connection():
    """
    Create a PostgreSQL database connection.

    If DATABASE_URL is available, it is used first. Otherwise, the app falls
    back to individual environment variables for local development.
    """
    if DATABASE_URL:
        return psycopg.connect(DATABASE_URL)

    return psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )


BASE_DIR = Path(__file__).resolve().parent
PULL_DATA_SCRIPT = BASE_DIR / "module_2_code" / "pull_new_data.py"

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


def fetch_one(cursor, query, params=None):
    """Execute a query and return the first value from the first row."""
    cursor.execute(query, params or ())
    return cursor.fetchone()[0]


def fetch_all(cursor, query, params=None):
    """Execute a query and return all result rows."""
    cursor.execute(query, params or ())
    return cursor.fetchall()


def get_filter_options():
    """Get dropdown filter options from the database."""
    options = {}

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT term
                FROM applicants
                WHERE term IS NOT NULL
                ORDER BY term
                LIMIT %s;
                """,
                (clamp_limit(100),)
            )
            options["terms"] = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                """
                SELECT degree
                FROM applicants
                WHERE degree IS NOT NULL
                GROUP BY degree
                HAVING COUNT(*) > 10
                ORDER BY degree
                LIMIT %s;
                """,
                (clamp_limit(100),)
            )
            options["degrees"] = [row[0] for row in cursor.fetchall()]

            options["statuses"] = ["Accepted", "Rejected", "Wait listed"]

            cursor.execute(
                """
                SELECT DISTINCT us_or_international
                FROM applicants
                WHERE us_or_international IS NOT NULL
                  AND us_or_international NOT IN ('0')
                ORDER BY us_or_international
                LIMIT %s;
                """,
                (clamp_limit(100),)
            )
            options["applicant_types"] = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                """
                SELECT DISTINCT llm_generated_university
                FROM applicants
                WHERE llm_generated_university IS NOT NULL
                  AND llm_generated_university ~ '^[A-Za-z0-9]'
                  AND llm_generated_university NOT ILIKE 'All %%'
                  AND llm_generated_university NOT ILIKE 'Any %%'
                  AND llm_generated_university NOT ILIKE '42 Us%%'
                  AND llm_generated_university NOT ILIKE 'Anywhere%%'
                  AND llm_generated_university NOT ILIKE 'N/A%%'
                ORDER BY llm_generated_university
                LIMIT %s;
                """,
                (clamp_limit(500),)
            )
            options["universities"] = [row[0] for row in cursor.fetchall()]

    return options


def build_filter_where_clause(filters):
    """
    Build a safe SQL WHERE clause and parameter list from dashboard filters.

    Column names are controlled by the application and values are passed
    separately through query parameters to avoid SQL injection.
    """
    where_clauses = []
    params = []

    filter_columns = {
        "term": "term",
        "degree": "degree",
        "status": "status",
        "applicant_type": "us_or_international",
        "university": "llm_generated_university",
    }

    for filter_key, column_name in filter_columns.items():
        filter_value = filters.get(filter_key)

        if filter_value:
            where_clauses.append(
                sql.SQL("{} = %s").format(sql.Identifier(column_name))
            )
            params.append(filter_value)

    if where_clauses:
        return sql.SQL("WHERE ") + sql.SQL(" AND ").join(where_clauses), params

    return sql.SQL(""), params


def get_condition_joiner(has_filters):
    """Return the correct SQL joiner for adding extra WHERE conditions."""
    if has_filters:
        return sql.SQL("AND")

    return sql.SQL("WHERE")


def get_dashboard_results(filters):
    """Get interactive dashboard metrics based on selected filters."""
    dashboard = {}
    where_sql, params = build_filter_where_clause(filters)
    has_filters = bool(params)
    condition_joiner = get_condition_joiner(has_filters)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            statement = sql.SQL(
                """
                SELECT COUNT(*)
                FROM applicants
                {}
                LIMIT %s;
                """
            ).format(where_sql)
            cursor.execute(statement, params + [1])
            dashboard["filtered_count"] = cursor.fetchone()[0]

            statement = sql.SQL(
                """
                SELECT ROUND(
                    100.0 * SUM(
                        CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END
                    )
                    / NULLIF(COUNT(*), 0),
                    2
                )
                FROM applicants
                {}
                LIMIT %s;
                """
            ).format(where_sql)
            cursor.execute(statement, params + [1])
            dashboard["acceptance_rate"] = cursor.fetchone()[0]

            statement = sql.SQL(
                """
                SELECT
                    ROUND(
                        AVG(CASE WHEN gpa BETWEEN 0.1 AND 4.0 THEN gpa END)::numeric,
                        2
                    ),
                    ROUND(
                        AVG(CASE WHEN gre BETWEEN 130 AND 170 THEN gre END)::numeric,
                        2
                    ),
                    ROUND(
                        AVG(CASE WHEN gre_v BETWEEN 130 AND 170 THEN gre_v END)::numeric,
                        2
                    ),
                    ROUND(
                        AVG(CASE WHEN gre_aw BETWEEN 0.5 AND 6.0 THEN gre_aw END)::numeric,
                        2
                    )
                FROM applicants
                {}
                LIMIT %s;
                """
            ).format(where_sql)
            cursor.execute(statement, params + [1])
            averages = cursor.fetchone()

            dashboard["average_gpa"] = averages[0]
            dashboard["average_gre_quant"] = averages[1]
            dashboard["average_gre_verbal"] = averages[2]
            dashboard["average_gre_aw"] = averages[3]

            statement = sql.SQL(
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
                        )
                        / NULLIF(COUNT(*), 0),
                        2
                    ) AS acceptance_rate
                FROM applicants
                {}
                {} llm_generated_university IS NOT NULL
                GROUP BY llm_generated_university
                ORDER BY total_entries DESC
                LIMIT %s;
                """
            ).format(where_sql, condition_joiner)
            cursor.execute(statement, params + [clamp_limit(10)])
            dashboard["top_universities"] = cursor.fetchall()

            dashboard["filtered_assignment_count"] = dashboard["filtered_count"]

            statement = sql.SQL(
                """
                SELECT ROUND(
                    100.0 * SUM(
                        CASE
                            WHEN us_or_international NOT IN ('American', 'Other', '0')
                            AND us_or_international IS NOT NULL
                            THEN 1 ELSE 0
                        END
                    ) / NULLIF(COUNT(*), 0),
                    2
                )
                FROM applicants
                {}
                LIMIT %s;
                """
            ).format(where_sql)
            cursor.execute(statement, params + [1])
            dashboard["filtered_percent_international"] = cursor.fetchone()[0]

            dashboard["filtered_acceptance_percent"] = dashboard["acceptance_rate"]

            statement = sql.SQL(
                """
                SELECT COUNT(*)
                FROM applicants
                {}
                {}
                    degree ILIKE %s
                    AND llm_generated_program ILIKE %s
                    AND llm_generated_university ILIKE %s
                LIMIT %s;
                """
            ).format(where_sql, condition_joiner)
            cursor.execute(
                statement,
                params + ["%Master%", "%Computer Science%", "%Johns Hopkins%", 1]
            )
            dashboard["filtered_jhu_masters_cs_count"] = cursor.fetchone()[0]

            statement = sql.SQL(
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
                {}
                {} llm_generated_university IS NOT NULL
                GROUP BY llm_generated_university
                HAVING COUNT(*) >= 5
                ORDER BY acceptance_rate ASC, total_entries DESC
                LIMIT %s;
                """
            ).format(where_sql, condition_joiner)
            cursor.execute(statement, params + [clamp_limit(10)])
            dashboard["filtered_competitive_universities"] = cursor.fetchall()

            statement = sql.SQL(
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
                {}
                {} degree IS NOT NULL
                GROUP BY degree
                HAVING COUNT(*) >= 5
                ORDER BY acceptance_rate DESC, total_entries DESC
                LIMIT %s;
                """
            ).format(where_sql, condition_joiner)
            cursor.execute(statement, params + [clamp_limit(100)])
            dashboard["filtered_degree_acceptance_rates"] = cursor.fetchall()

    return dashboard


def get_analysis_results():
    """Return dashboard data for the analysis page."""
    results = {}

    with get_connection() as connection:
        with connection.cursor() as cursor:
            results["fall_2026_count"] = fetch_one(
                cursor,
                """
                SELECT COUNT(*)
                FROM applicants
                WHERE term = 'Fall 2026'
                LIMIT 1;
                """
            )

            results["percent_international"] = fetch_one(
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

            results["average_metrics"] = {
                "gpa": round(q3[0], 2) if q3[0] is not None else None,
                "gre_quant": round(q3[1], 2) if q3[1] is not None else None,
                "gre_verbal": round(q3[2], 2) if q3[2] is not None else None,
                "gre_aw": round(q3[3], 2) if q3[3] is not None else None,
            }

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
            results["american_fall_2026_avg_gpa"] = fetch_one(cursor, q4_query)

            results["fall_2026_acceptance_percent"] = fetch_one(
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
            results["accepted_fall_2026_avg_gpa"] = fetch_one(cursor, q6_query)

            results["jhu_masters_cs_count"] = fetch_one(
                cursor,
                """
                SELECT COUNT(*)
                FROM applicants
                WHERE degree ILIKE '%%Master%%'
                AND llm_generated_program ILIKE '%%Computer Science%%'
                AND llm_generated_university ILIKE '%%Johns Hopkins%%'
                LIMIT 1;
                """
            )

            results["q8_downloaded_fields_count"] = fetch_one(
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

            results["q9_llm_fields_count"] = fetch_one(
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

            results["competitive_universities"] = fetch_all(
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
                LIMIT 10;
                """
            )

            results["degree_acceptance_rates"] = fetch_all(
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
                LIMIT 100;
                """
            )

    return results


def run_pull_data_pipeline():
    """Run the incremental Pull Data pipeline in the background."""
    global PULL_DATA_RUNNING  # pylint: disable=global-statement

    try:
        print("Starting Pull Data pipeline from Flask...")

        subprocess.run(
            [sys.executable, str(PULL_DATA_SCRIPT)],
            check=True,
            cwd=BASE_DIR
        )

        print("Pull Data pipeline finished successfully.")

    except subprocess.CalledProcessError as error:
        print(f"Pull Data pipeline failed: {error}")

    finally:
        with PULL_DATA_LOCK:
            PULL_DATA_RUNNING = False


app = create_app()

if __name__ == "__main__":  # pragma: no cover
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)  # pragma: no cover
