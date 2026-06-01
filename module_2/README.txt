Name: Karunya, knaraya7

Module Info:
Module 2 - Web Scraping
Due Date: 31 May 2026, 11:59PM

Approach:
For this assignment, I built a web scraper to collect publicly accessible Grad Cafe applicant data and save it into a structured JSON file for later analysis. To accomplish this, I followed an incremental development process. 

Step 1: After creating the folder structure and the required Python files and JSON files, I checked Grad Cafe’s robots.txt file, and saved evidence of that check as screenshot.jpg.
- Before scraping, I reviewed Grad Cafe’s robots.txt file at https://www.thegradcafe.com/robots.txt. The robots.txt file included a general User-agent rule with Allow: /, and the project only scrapes publicly accessible Grad Cafe survey pages. The scraper does not access login-protected pages, private pages, restricted pages, CAPTCHA-protected pages, or disallowed content. The scraper also includes delays between requests and stops if a request fails, times out, or is rejected.

Step 2: Implementing scraping logic using urlib to construct URLs into scrape.py, I tested the scraper on one public Grad Cafe survey page filtered by Computer Science results. 
- After inspecting the returned HTML, I found that applicant result data was already embedded in the HTML response inside the div with id="app", specifically in the data-page attribute. Because the applicant records were available in the static HTML returned by urllib, Selenium was not necessary for this implementation.
- The scraper uses BeautifulSoup to locate the div with id="app". The value of its data-page attribute is HTML-escaped, so I used Python’s html module to unescape it. I then used json.loads() to convert the embedded page data into a Python dictionary. From that dictionary, I extracted the applicant records from props → results → data.

Step 3: I then developed the scraper in stages, from 20 records to 5 pages to then 50 pages for 1000 records and then eventually to scrape 30,000 records. When scraping 30,000 records, I added progress-saving to scrape.py. 
- The scraper saves raw applicant records to raw_applicant_data.json after every page. This prevents data loss if the script stops due to a timeout or connection issue. I also added duplicate protection using the Grad Cafe applicant id field. When the scraper resumes or restarts, it loads previously saved records, stores their IDs in a set, and only adds records whose IDs have not already been collected.

Step 4: This then leads me to clean.py where I implemented my cleaning logic. This file loads raw_applicant_data.json, converts the raw fields into descriptive ready fields based on assignment requirements, and saves the structured output to applicant_data.json.
- This cleaning step preserves both a human-readable raw_text field and the original raw_record dictionary for traceability and reproducibility.
- The cleaned applicant records include fields such as program_name, university, comments, date_added, entry_url, applicant_status, acceptance_date, rejection_date, program_start, student_type, degree_type, GPA, GRE-related fields, Grad Cafe ID, raw_text, and raw_record. Missing or unavailable values are preserved as null in JSON.
- For GRE data, I mapped the raw Grad Cafe GRE fields into clearer names. The raw Grad Cafe field greq is stored as gre_qr_score, representing GRE Quantitative Reasoning. The raw field grev is stored as gre_vr_score, representing GRE Verbal Reasoning. The raw field grew is stored as gre_aw_score, representing GRE Analytical Writing. Referring to https://test-ninjas.com/gre-score-calculator, I calculated gre_score as gre_qr_score + gre_vr_score when both values were available and could be converted to integers. If either component was missing or invalid, gre_score was stored as null.

Step 5: Once applicant_data.json had been generated, I used the provided llm_hosting package standardize the messy program and university names.
- This tool reads the cleaned applicant data and appends two additional fields: llm-generated-program and llm-generated-university. This step addresses the issue where program and university names can appear in inconsistent forms, such as abbreviations, misspellings, or mixed program/university labels. The LLM-extended output was saved as llm_extend_applicant_data.json.

The final output files are 
- applicant_data.json, which contains cleaned structured applicant records, and 
- llm_extend_applicant_data.json, which contains LLM-extended records with standardized program and university fields. 
I validated that the llm_extend_applicant_data.json is valid JSON, contains 30,000 records, and includes the LLM-generated fields.

Known Bugs/ Limitations:
- The downloaded TinyLlama .gguf model file is not included in the GitHub repository because it is too large and is generated/downloaded at runtime