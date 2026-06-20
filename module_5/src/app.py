"""Flask application for displaying Grad Cafe analysis results."""

import os
from pathlib import Path
import subprocess
import sys
import threading
import psycopg
from flask import Flask, render_template, request, redirect, url_for, jsonify

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

    # routes will go here
    @flask_app.route("/")
    def home():
        return redirect(url_for("analysis"))


    @flask_app.route("/analysis")
    def analysis():
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
        Starts the incremental data pull pipeline.

        Returns JSON so tests and the webpage can check whether the pull started.
        """
        global PULL_DATA_RUNNING    # pylint: disable=global-statement

        with PULL_DATA_LOCK:
            if PULL_DATA_RUNNING:
                return jsonify({
                    "ok": False,
                    "busy": True,
                    "message":
                        "Pull Data is already running. "
                        "Please wait before starting another request."
                }), 409

            PULL_DATA_RUNNING = True

        pipeline_thread = threading.Thread(target=run_pull_data_pipeline)
        pipeline_thread.start()

        return jsonify({
            "ok": True,
            "busy": False,
            "message": "Pull Data has started. The app is checking Grad Café for new records."
        }), 202

    @flask_app.route("/update-analysis", methods=["POST"])
    def update_analysis():
        """
        Refreshes analysis unless Pull Data is currently running.

        Returns JSON so tests and the webpage can check the update status.
        """
        if PULL_DATA_RUNNING:
            return jsonify({
                "ok": False,
                "busy": True,
                "message":
                    "Analysis cannot be updated while Pull Data is running. "
                    "Please wait and try again."
            }), 409

        return jsonify({
            "ok": True,
            "busy": False,
            "message": "Analysis updated using the current PostgreSQL database."
        }), 200


    return flask_app

# ------------------------------
# Database connection settings
# ------------------------------

DATABASE_URL = os.environ.get("DATABASE_URL")

DB_NAME = "gradcafe_db"
DB_USER = "postgres"
DB_PASSWORD = "jscm3@56psg"
DB_HOST = "localhost"
DB_PORT = "5432"

def get_connection():
    """
    Creates a PostgreSQL database connection.

    If DATABASE_URL is available, it is used first. This is useful for tests
    and GitHub Actions. Otherwise, the app falls back to the local PostgreSQL
    settings used for development.
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


def fetch_one(cursor, query, params=None):
    """Execute a query and return the first value from the first row."""
    cursor.execute(query, params or ())
    return cursor.fetchone()[0]


def fetch_all(cursor, query, params=None):
    """Execute a query and return all result rows."""
    cursor.execute(query, params or ())
    return cursor.fetchall()

def get_filter_options():
    """Gets dropdown filter options from the database."""
    options = {}

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT term
                FROM applicants
                WHERE term IS NOT NULL
                ORDER BY term;
            """)
            options["terms"] = [row[0] for row in cursor.fetchall()]

            cursor.execute("""
                SELECT degree
                FROM applicants
                WHERE degree IS NOT NULL
                GROUP BY degree
                HAVING COUNT(*) > 10
                ORDER BY degree;
            """)
            options["degrees"] = [row[0] for row in cursor.fetchall()]

            # Only include the 3 useful admission decision statuses
            options["statuses"] = ["Accepted", "Rejected", "Wait listed"]

            cursor.execute("""
                SELECT DISTINCT us_or_international
                FROM applicants
                WHERE us_or_international IS NOT NULL
                  AND us_or_international NOT IN ('0')
                ORDER BY us_or_international;
            """)
            options["applicant_types"] = [row[0] for row in cursor.fetchall()]

            cursor.execute("""
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
                LIMIT 500;
            """)
            options["universities"] = [row[0] for row in cursor.fetchall()]

    return options


def build_filter_where_clause(filters):
    """
    Builds a dynamic SQL WHERE clause based on dashboard filters.
    Uses parameters to avoid unsafe string formatting.
    """
    where_clauses = []
    params = []

    if filters.get("term"):
        where_clauses.append("term = %s")
        params.append(filters["term"])

    if filters.get("degree"):
        where_clauses.append("degree = %s")
        params.append(filters["degree"])

    if filters.get("status"):
        where_clauses.append("status = %s")
        params.append(filters["status"])

    if filters.get("applicant_type"):
        where_clauses.append("us_or_international = %s")
        params.append(filters["applicant_type"])

    if filters.get("university"):
        where_clauses.append("llm_generated_university = %s")
        params.append(filters["university"])

    if where_clauses:
        return "WHERE " + " AND ".join(where_clauses), params

    return "", params


def get_dashboard_results(filters):
    """
    Gets interactive dashboard metrics based on selected filters.
    """
    dashboard = {}
    where_sql, params = build_filter_where_clause(filters)

    with get_connection() as connection:
        with connection.cursor() as cursor:

            # General filtered count
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM applicants
                {where_sql};
            """, params)
            dashboard["filtered_count"] = cursor.fetchone()[0]

            # General filtered acceptance rate
            cursor.execute(f"""
                SELECT ROUND(
                    100.0 * SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END)
                    / NULLIF(COUNT(*), 0),
                    2
                )
                FROM applicants
                {where_sql};
            """, params)
            dashboard["acceptance_rate"] = cursor.fetchone()[0]

            # General filtered averages
            cursor.execute(f"""
                SELECT
                    ROUND(AVG(CASE WHEN gpa BETWEEN 0.1 AND 4.0 THEN gpa END)::numeric, 2),
                    ROUND(AVG(CASE WHEN gre BETWEEN 130 AND 170 THEN gre END)::numeric, 2),
                    ROUND(AVG(CASE WHEN gre_v BETWEEN 130 AND 170 THEN gre_v END)::numeric, 2),
                    ROUND(AVG(CASE WHEN gre_aw BETWEEN 0.5 AND 6.0 THEN gre_aw END)::numeric, 2)
                FROM applicants
                {where_sql};
            """, params)
            averages = cursor.fetchone()

            dashboard["average_gpa"] = averages[0]
            dashboard["average_gre_quant"] = averages[1]
            dashboard["average_gre_verbal"] = averages[2]
            dashboard["average_gre_aw"] = averages[3]

            # Top universities within current filter
            cursor.execute(f"""
                SELECT
                    llm_generated_university,
                    COUNT(*) AS total_entries,
                    SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) AS accepted_entries,
                    ROUND(
                        100.0 * SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END)
                        / NULLIF(COUNT(*), 0),
                        2
                    ) AS acceptance_rate
                FROM applicants
                {where_sql}
                {"AND" if where_sql else "WHERE"} llm_generated_university IS NOT NULL
                GROUP BY llm_generated_university
                ORDER BY total_entries DESC
                LIMIT 10;
            """, params)
            dashboard["top_universities"] = cursor.fetchall()

            # Assignment-style filtered Q1:
            # Count entries in current filter
            dashboard["filtered_assignment_count"] = dashboard["filtered_count"]

            # Assignment-style filtered Q2:
            # Percent international in current filter
            cursor.execute(f"""
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
                {where_sql};
            """, params)
            dashboard["filtered_percent_international"] = cursor.fetchone()[0]

            # Assignment-style filtered Q5:
            # Acceptance percent in current filter
            dashboard["filtered_acceptance_percent"] = dashboard["acceptance_rate"]

            # Assignment-style filtered Q7:
            # JHU Master's CS count within current filter
            extra_conditions = """
                degree ILIKE '%%Master%%'
                AND llm_generated_program ILIKE '%%Computer Science%%'
                AND llm_generated_university ILIKE '%%Johns Hopkins%%'
            """

            cursor.execute(f"""
                SELECT COUNT(*)
                FROM applicants
                {where_sql}
                {"AND" if where_sql else "WHERE"} {extra_conditions};
            """, params)
            dashboard["filtered_jhu_masters_cs_count"] = cursor.fetchone()[0]

            # Most competitive universities within current filter
            cursor.execute(f"""
                SELECT
                    llm_generated_university,
                    COUNT(*) AS total_entries,
                    SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) AS accepted_entries,
                    ROUND(
                        100.0 * SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) / COUNT(*),
                        2
                    ) AS acceptance_rate
                FROM applicants
                {where_sql}
                {"AND" if where_sql else "WHERE"} llm_generated_university IS NOT NULL
                GROUP BY llm_generated_university
                HAVING COUNT(*) >= 5
                ORDER BY acceptance_rate ASC, total_entries DESC
                LIMIT 10;
            """, params)
            dashboard["filtered_competitive_universities"] = cursor.fetchall()

            # Degree acceptance rate within current filter
            cursor.execute(f"""
                SELECT
                    degree,
                    COUNT(*) AS total_entries,
                    SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) AS accepted_entries,
                    ROUND(
                        100.0 * SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) / COUNT(*),
                        2
                    ) AS acceptance_rate
                FROM applicants
                {where_sql}
                {"AND" if where_sql else "WHERE"} degree IS NOT NULL
                GROUP BY degree
                HAVING COUNT(*) >= 5
                ORDER BY acceptance_rate DESC, total_entries DESC;
            """, params)
            dashboard["filtered_degree_acceptance_rates"] = cursor.fetchall()

    return dashboard


def get_analysis_results():
    """Return dashboard data for the analysis page."""
    results = {}

    with get_connection() as connection:
        with connection.cursor() as cursor:

            # Q1
            results["fall_2026_count"] = fetch_one(cursor, """
                SELECT COUNT(*)
                FROM applicants
                WHERE term = 'Fall 2026';
            """)

            # Q2
            results["percent_international"] = fetch_one(cursor, """
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
                            WHEN us_or_international IN ('American', 'International', 'Other')
                                OR COALESCE(comments, '') ILIKE '%%Canadian%%'
                                OR COALESCE(comments, '') ILIKE '%%International%%'
                                OR COALESCE(comments, '') ILIKE '%%US Citizen%%'
                                OR COALESCE(comments, '') ILIKE '%%American%%'
                            THEN 1 ELSE 0
                        END
                    ),
                    2
                )
                FROM applicants;
            """)

            # Q3
            q3 = fetch_all(cursor, f"""
                SELECT
                    AVG({NORMALIZED_GPA_SQL}) AS average_gpa,
                    AVG(CASE WHEN gre BETWEEN 130 AND 170 THEN gre END) AS average_gre_quant,
                    AVG(CASE WHEN gre_v BETWEEN 130 AND 170 THEN gre_v END) AS average_gre_verbal,
                    AVG(CASE WHEN gre_aw BETWEEN 0.1 AND 6.0 THEN gre_aw END) AS average_gre_aw
                FROM applicants;
            """)[0]

            results["average_metrics"] = {
                "gpa": round(q3[0], 2) if q3[0] is not None else None,
                "gre_quant": round(q3[1], 2) if q3[1] is not None else None,
                "gre_verbal": round(q3[2], 2) if q3[2] is not None else None,
                "gre_aw": round(q3[3], 2) if q3[3] is not None else None,
            }

            # Q4
            results["american_fall_2026_avg_gpa"] = fetch_one(cursor, f"""
                SELECT ROUND(AVG({NORMALIZED_GPA_SQL})::numeric, 2)
                FROM applicants
                WHERE term = 'Fall 2026'
                AND (
                    us_or_international = 'American'
                    OR comments ILIKE '%%US Citizen%%'
                )
                AND {NORMALIZED_GPA_SQL} IS NOT NULL;
            """)

            # Q5
            results["fall_2026_acceptance_percent"] = fetch_one(cursor, """
                SELECT ROUND(
                    100.0 * SUM(
                        CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END
                    ) / COUNT(*),
                    2
                )
                FROM applicants
                WHERE term = 'Fall 2026';
            """)

            # Q6
            results["accepted_fall_2026_avg_gpa"] = fetch_one(cursor, f"""
                SELECT ROUND(AVG({NORMALIZED_GPA_SQL})::numeric, 2)
                FROM applicants
                WHERE term = 'Fall 2026'
                AND status = 'Accepted'
                AND {NORMALIZED_GPA_SQL} IS NOT NULL;
            """)

            # Q7
            results["jhu_masters_cs_count"] = fetch_one(cursor, """
                SELECT COUNT(*)
                FROM applicants
                WHERE degree ILIKE '%%Master%%'
                AND llm_generated_program ILIKE '%%Computer Science%%'
                AND llm_generated_university ILIKE '%%Johns Hopkins%%';
            """)

            # Q8
            results["q8_downloaded_fields_count"] = fetch_one(cursor, """
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
                );
            """)

            # Q9
            results["q9_llm_fields_count"] = fetch_one(cursor, """
                SELECT COUNT(*)
                FROM applicants
                WHERE term ILIKE '%%2026%%'
                AND status = 'Accepted'
                AND degree ILIKE '%%PhD%%'
                AND llm_generated_program ILIKE '%%Computer Science%%'
                AND (
                    llm_generated_university ILIKE '%%Georgetown%%'
                    OR llm_generated_university ILIKE '%%Massachusetts Institute of Technology%%'
                    OR llm_generated_university ILIKE '%%MIT%%'
                    OR llm_generated_university ILIKE '%%Stanford%%'
                    OR llm_generated_university ILIKE '%%Carnegie Mellon%%'
                    OR llm_generated_university ILIKE '%%CMU%%'
                );
            """)

            # Q10
            results["competitive_universities"] = fetch_all(cursor, """
                SELECT
                    llm_generated_university,
                    COUNT(*) AS total_entries,
                    SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) AS accepted_entries,
                    ROUND(
                        100.0 * SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) / COUNT(*),
                        2
                    ) AS acceptance_rate
                FROM applicants
                WHERE term = 'Fall 2026'
                AND llm_generated_university IS NOT NULL
                GROUP BY llm_generated_university
                HAVING COUNT(*) >= 10
                ORDER BY acceptance_rate ASC, total_entries DESC
                LIMIT 10;
            """)

            # Q11
            results["degree_acceptance_rates"] = fetch_all(cursor, """
                SELECT
                    degree,
                    COUNT(*) AS total_entries,
                    SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) AS accepted_entries,
                    ROUND(
                        100.0 * SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) / COUNT(*),
                        2
                    ) AS acceptance_rate
                FROM applicants
                WHERE term = 'Fall 2026'
                AND degree IS NOT NULL
                GROUP BY degree
                HAVING COUNT(*) >= 10
                ORDER BY acceptance_rate DESC;
            """)

    return results


def run_pull_data_pipeline():
    """
    Runs the incremental Pull Data pipeline in the background.
    """
    global PULL_DATA_RUNNING    # pylint: disable=global-statement

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
    app.run(debug=True)  # pragma: no cover
