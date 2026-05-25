# Flask is the main class used to create a web application.
from flask import Flask

# Import the blueprint called "pages" from pages.py.
# A blueprint helps organize routes/pages in a Flask website.
from personal_site.pages import pages


def create_app():
    """
    Create and configure the Flask application.

    This function 
    1. Creates a new Flask application
    2. Registers the pages blueprint with the app which connects the routes in pages.py to the main website
    3. Returns the finished Flask app so run.py can start it
    """

    app = Flask(__name__)

    app.register_blueprint(pages)

    return app