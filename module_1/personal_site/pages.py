from flask import Blueprint, render_template


# creating a blueprint with name pages
# this blueprint will hold the routes for the website pages
pages = Blueprint("pages", __name__)


@pages.route("/")
def home():
    """
    Display the homepage.

    The homepage includes:
    - name
    - position
    - biography
    - image
    """

    return render_template("home.html", active_page="home")


@pages.route("/contact")
def contact():
    """
    Display the contact page.

    The contact page includes:
    - email address
    - LinkedIn information
    """

    
    return render_template("contact.html", active_page="contact")


@pages.route("/projects")
def projects():
    """
    Display the projects page.

    The projects page includes:
    - Module 1 project title
    - project details
    - GitHub project link
    """

    return render_template("projects.html", active_page="projects")