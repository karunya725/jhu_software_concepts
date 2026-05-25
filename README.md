## Module 1 Assignment: Personal Website

### This assignment involves developing a personal website using Python, Flask, HTML and CSS which includes:
- A homepage with a short biography and profile image
- A contact page with email and LinkedIn information
- A projects page with details about the Module 1 project
- A navigation bar that links to all pages
- Styling using CSS and Bootstrap

### Required Python Version:
Python 3.10 or higher

### How to Run the Website:
1. Open a terminal or PowerShell window.

2. Install the required Python packages.
   
    Run: "pip install -r requirements.txt" OR "py -m pip install -r requirements.txt"

3. Start the Flask application.

    Run: "python run.py" OR "py run.py"

4. Open a web browser and go to: http://localhost:8080

    The website will run locally on port 8080.

### Project Structure:
module_1/
- run.py
- requirements.txt
- README.txt
- screenshots.pdf
- personal_site/
  - __init__.py
  - create_app.py
  - pages.py
  - static/
    - style.css
    - profile.jpg
  - templates/
    - base.html
    - home.html
    - contact.html
    - projects.html