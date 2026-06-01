Name:
Karunya knaraya7

Module Info:
Module 2 - Grad Cafe Applicant Data Scraper
Due Date: [ADD DUE DATE HERE]

Approach:
!!! Rewrite this apprach !!! 
This project will scrape publicly accessible Grad Cafe applicant data, clean the scraped entries, and save the structured applicant records as JSON.

The scraper will use urllib to construct, inspect, and manage Grad Cafe URLs. If needed, Selenium will be used to render public Grad Cafe pages, and BeautifulSoup, regex, and Python string methods will be used to parse applicant data from the rendered HTML.

The first output file will be applicant_data.json. This file will contain the scraped applicant entries with descriptive JSON keys and preserved raw applicant listing text for traceability.

The second output file will be llm_extend_applicant_data.json. This file will contain the cleaned/extended version after running the provided local LLM standardization tool inside module_2/llm_hosting.
!!! Rewrite this apprach !!! 

GRE field mapping:
The Grad Cafe raw data uses greq, grev, and grew. In this project, greq is stored as gre_qr_score, representing GRE Quantitative Reasoning. grev is stored as gre_vr_score, representing GRE Verbal Reasoning. grew is stored as gre_aw_score, representing GRE Analytical Writing.

The total gre_score field is calculated as gre_qr_score + gre_vr_score when both values are available. If either Quantitative Reasoning or Verbal Reasoning is missing or cannot be converted to an integer, gre_score is stored as null.

Robots.txt Compliance:
!!! Rewrite this apprach !!! 
Before scraping Grad Cafe, I checked the site's robots.txt file at https://www.thegradcafe.com/robots.txt. Evidence of this check is included in this folder as screenshot.jpg.

The robots.txt file showed a general rule for "User-agent: *" with "Allow: /", which indicates that general publicly accessible pages are allowed for that user-agent group. The file also included the content signal "search=yes, ai-train=no". This project does not train or fine-tune an AI model using Grad Cafe content.

Based on this check, the scraper is designed to collect only publicly accessible Grad Cafe applicant pages. The scraper will not access login-protected, private, restricted, CAPTCHA-protected, or disallowed pages. The scraper will also stop if the site blocks, rate-limits, or rejects requests.
!!! Rewrite this apprach !!! 

Known Bugs:
!!! Rewrite this apprach !!! 
Not applicable yet. This section will be updated after implementation and testing.
!!! Rewrite this apprach !!! 