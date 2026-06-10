!!! MODIFY THIS ENTIRE PAGE !!! 

Name: Karunya, knaraya7

Module Info: Module 3 - Database Queries
Due Date: 07 Jun 2026, 11:59PM

GitHub SSH URL:
git@github.com:karunya725/jhu_software_concepts.git

Project Approach:

For this assignment, I used the cleaned Grad Café applicant data from Module 2 and loaded it into a PostgreSQL database containing one main table called applicants. I then wrote SQL queries in query_data.py to answer the assignment questions. I also created a Flask web application that connects to the PostgreSQL database and displays the analysis results dynamically. The webpage includes two tabs: Assignment Analysis for the required SQL results, and Exploring the Dataset for an interactive dashboard with filters.

For Part B, I copied my Module 2 scraping and cleaning code into the module_3/module_2_code folder. The Pull Data button runs an incremental data pipeline that checks Grad Café for newly available Computer Science records, cleans only the new records, runs LLM enrichment only on the new cleaned records, and inserts the new records into PostgreSQL without resetting the existing database. The Update Analysis button refreshes the displayed analysis using the current PostgreSQL database.

How to Run the Full Web Application:

1. Install PostgreSQL and create the database.

    Create a PostgreSQL database named: gradcafe_db

2. Install the Python dependencies.

    From inside the module_3 folder, run: py -m pip install -r requirements.txt

3. Check the database connection settings.

    In these files, make sure the PostgreSQL database settings match your local setup:

    load_data.py
    query_data.py
    app.py

    The expected database settings are:

    Database name: gradcafe_db
    User: postgres
    Host: localhost
    Port: 5432

4. Load the initial dataset into PostgreSQL.

    From inside the module_3 folder, run: py load_data.py

    This creates the applicants table and loads the baseline records from: data/llm_extend_applicant_data.json

5. Run the console SQL analysis.

    From inside the module_3 folder, run: py query_data.py

    This prints the answers to the required assignment questions and the two additional questions.

6. Run the Flask web application.

    From inside the module_3 folder, run: py app.py

    Then open this URL in a browser: http://127.0.0.1:5000

7. Use the webpage.

    The Assignment Analysis tab shows the required SQL analysis results.

    The Exploring the Dataset tab contains dashboard filters and filtered analysis results.

    The Pull Data button runs the incremental scraping and cleaning pipeline:

        module_2_code/scrape.py
        module_2_code/clean_new_data.py
        module_2_code/run_llm_on_new_data.py
        module_2_code/insert_new_data.py

    The Update Analysis button refreshes the analysis using the current PostgreSQL database.

Known Bugs / Limitations:

- The application depends on a local PostgreSQL setup. It will not run correctly unless PostgreSQL is installed, the gradcafe_db database exists, and the database credentials in the Python files match the user’s local setup.

- The LLM enrichment step can be slow if many new records are found. To make the workflow more efficient, the pipeline only runs LLM enrichment on newly scraped records, not on the full dataset.

- The local LLM model files are not included in GitHub because they are too large. The llm_hosting/models folder and .gguf model files are intentionally ignored by Git. Anyone running the LLM enrichment step locally must provide the required model file separately.

- Some dashboard filters rely on LLM-generated program and university fields. These fields are cleaner than the original downloaded program string, but they may still contain occasional LLM classification errors.

- The Pull Data button runs the data pipeline in the background. The page auto-refreshes while the pull is running, but if the page state looks stale, manually refreshing the browser will update the button state.
