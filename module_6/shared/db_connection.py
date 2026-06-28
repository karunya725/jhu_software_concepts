"""Shared PostgreSQL connection helpers for Module 6 services."""

import os

import psycopg


DATABASE_URL = os.environ.get("DATABASE_URL")

DB_NAME = os.environ.get("DB_NAME", "gradcafe_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")


def get_connection():
    """Create and return a PostgreSQL database connection."""
    if DATABASE_URL:
        return psycopg.connect(DATABASE_URL)

    return psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
