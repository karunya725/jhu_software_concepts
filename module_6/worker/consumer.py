"""Temporary worker service for Module 6 Docker Compose setup."""

import os
import time


def main():
    """Start a placeholder worker loop."""
    print("Worker container started.", flush=True)
    print(f"DATABASE_URL set: {bool(os.environ.get('DATABASE_URL'))}", flush=True)
    print(f"RABBITMQ_URL set: {bool(os.environ.get('RABBITMQ_URL'))}", flush=True)

    while True:
        print("Worker is alive.", flush=True)
        time.sleep(30)


if __name__ == "__main__":
    main()