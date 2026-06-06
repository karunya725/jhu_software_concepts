import psycopg


# -----------------------------
# Database connection settings
# -----------------------------
DB_NAME = "gradcafe_db"
DB_USER = "postgres"
DB_PASSWORD = "jscm3@56psg"
DB_HOST = "localhost"
DB_PORT = "5432"


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


def get_connection():
    return psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )


def fetch_one(cursor, query, params=None):
    cursor.execute(query, params or ())
    return cursor.fetchone()[0]


def fetch_all(cursor, query, params=None):
    cursor.execute(query, params or ())
    return cursor.fetchall()


def main():
    with get_connection() as connection:
        with connection.cursor() as cursor:

            print("\nGrad Cafe Data Analysis")
            print("=" * 50)

            # Q1: Fall applicant count
            q1 = fetch_one(cursor, """
                SELECT COUNT(*)
                FROM applicants
                WHERE term = 'Fall 2026';
            """)
            print(f"\n1. Fall 2026 applicant count: {q1}")

            # Q2: Percentage of international students
            # Some nationality values are invalid, such as '0', so this query also checks comments for nationality clues. 
            # Comments containing "Canadian" or "International" are treated as international
            # while comments containing "US Citizen" or "American" are treated as American
            q2 = fetch_one(cursor, """
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
            print(f"2. Percent international: {q2}%")

            # Q3: Average GPA, GRE, GRE V, GRE AW of applicants
            # GRE scores range from 130 to 170 in the separate Verbal and Quant sections
            # GRE AW uses 0.1–6.0 here because 0 is treated as likely missing or unusable in this scraped dataset
            q3 = fetch_all(cursor, f"""
                SELECT
                    AVG({NORMALIZED_GPA_SQL}) AS average_gpa,
                    AVG(CASE WHEN gre BETWEEN 130 AND 170 THEN gre END) AS average_gre_quant,
                    AVG(CASE WHEN gre_v BETWEEN 130 AND 170 THEN gre_v END) AS average_gre_verbal,
                    AVG(CASE WHEN gre_aw BETWEEN 0.1 AND 6.0 THEN gre_aw END) AS average_gre_aw
                FROM applicants;
            """)[0]

            print(
                "3. Average metrics: "
                f"GPA = {round(q3[0], 2) if q3[0] is not None else None}, "
                f"GRE Quant = {round(q3[1], 2) if q3[1] is not None else None}, "
                f"GRE Verbal = {round(q3[2], 2) if q3[2] is not None else None}, "
                f"GRE AW = {round(q3[3], 2) if q3[3] is not None else None}"
            )

            # Q4: Average GPA of American students in Fall 2026
            q4 = fetch_one(cursor, f"""
                SELECT ROUND(AVG({NORMALIZED_GPA_SQL})::numeric, 2)
                FROM applicants
                WHERE term = 'Fall 2026'
                AND (
                    us_or_international = 'American'
                    OR comments ILIKE '%%US Citizen%%'
                )
                AND {NORMALIZED_GPA_SQL} IS NOT NULL;
            """)

            print(f"4. Average normalized GPA of American students in Fall 2026: {q4}")

            # Q5: Percentage of Fall 2026 acceptance
            q5 = fetch_one(cursor, """
                SELECT ROUND(
                    100.0 * SUM(
                        CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END
                    ) / COUNT(*),
                    2
                )
                FROM applicants
                WHERE term = 'Fall 2026';
            """)
            print(f"5. Fall 2026 acceptance percent: {q5}%")

            # Q6: Average GPA of applicants who applied for Fall 2026 who are Acceptances
            q6 = fetch_one(cursor, f"""
                SELECT ROUND(AVG({NORMALIZED_GPA_SQL})::numeric, 2)
                FROM applicants
                WHERE term = 'Fall 2026'
                AND status = 'Accepted'
                AND {NORMALIZED_GPA_SQL} IS NOT NULL;
            """)

            print(f"6. Average normalized GPA of accepted Fall 2026 applicants: {q6}")

            # Q7: JHU Master's Computer Science count
            q7 = fetch_one(cursor, """
                SELECT COUNT(*) AS jhu_masters_cs_count
                FROM applicants
                WHERE degree ILIKE '%%Master%%'
                AND llm_generated_program ILIKE '%%Computer Science%%'
                AND llm_generated_university ILIKE '%%Johns Hopkins%%';
            """)
            print(f"7. JHU Master's Computer Science count: {q7}")

            # Q8
            q8 = fetch_one(cursor, """
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
            print(
                "8. 2026 acceptances to Georgetown/MIT/Stanford/CMU "
                f"for PhD Computer Science using downloaded fields: {q8}"
            )

            # Q9
            q9 = fetch_one(cursor, """
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
            print(
                "9. 2026 acceptances to Georgetown/MIT/Stanford/CMU "
                f"for PhD Computer Science using LLM-generated fields: {q9}"
            )

            # Q10 - (Possible) Additional question 1
            print("\n10. Which universities appear most competitive in Fall 2026 based on low acceptance rate?")
            q10 = fetch_all(cursor, """
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

            for row in q10:
                print(
                    f"    {row[0]}: {row[2]} accepted out of {row[1]} "
                    f"({row[3]}% acceptance rate)"
                )


            # Q11 - (Possible) Additional question 2
            print("\n11. Are international applicants over or under represented among Fall 2026 Computer Science applicants?")
            q11 = fetch_all(cursor, """
                SELECT
                    us_or_international,
                    COUNT(*) AS total_entries,
                    ROUND(
                        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (),
                        2
                    ) AS percent_of_fall_2026_cs_entries
                FROM applicants
                WHERE term = 'Fall 2026'
                AND llm_generated_program ILIKE '%%Computer Science%%'
                AND us_or_international IS NOT NULL
                AND us_or_international NOT IN ('0')
                GROUP BY us_or_international
                ORDER BY total_entries DESC;
            """)

            for row in q11:
                print(
                    f"    {row[0]}: {row[1]} entries "
                    f"({row[2]}% of Fall 2026 Computer Science entries)"
                )

            print("\n" + "=" * 50)
            print("Analysis complete.\n")


if __name__ == "__main__":
    main()