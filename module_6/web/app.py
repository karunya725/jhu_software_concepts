"""Temporary Flask web service for Module 6 Docker Compose setup."""

import os

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    """Basic health page for the web container."""
    return jsonify(
        {
            "status": "ok",
            "service": "web",
            "database_url_set": bool(os.environ.get("DATABASE_URL")),
            "rabbitmq_url_set": bool(os.environ.get("RABBITMQ_URL")),
        }
    )


@app.route("/analysis")
def analysis():
    """Temporary analysis route for Docker setup verification."""
    return jsonify(
        {
            "status": "ok",
            "message": "Module 6 web container is running.",
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)