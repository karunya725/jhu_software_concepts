from personal_site import create_app

# creating Flask application by calling the create_app function
app = create_app()

# when we start the program with run.py, the Flask development server will start & the site will run locally
if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)