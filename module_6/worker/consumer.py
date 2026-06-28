"""RabbitMQ consumer for Grad Cafe background tasks."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pika

from shared.rabbitmq_helpers import open_task_channel


BASE_DIR = Path(__file__).resolve().parent
PULL_DATA_SCRIPT = BASE_DIR / "module_2_code" / "pull_new_data.py"

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbit:5672/")

EXCHANGE_NAME = "tasks"
QUEUE_NAME = "tasks_q"
ROUTING_KEY = "tasks"

HEARTBEAT_SECONDS = 1800
BLOCKED_CONNECTION_TIMEOUT_SECONDS = 1800
RETRY_DELAY_SECONDS = 5


def open_channel():
    """Open RabbitMQ connection and declare durable task infrastructure."""
    connection, channel = open_task_channel(
        RABBITMQ_URL,
        EXCHANGE_NAME,
        QUEUE_NAME,
        ROUTING_KEY,
    )
    channel.basic_qos(prefetch_count=1)
    return connection, channel


def run_pull_data_pipeline():
    """Run the full Pull Data pipeline in the worker container."""
    print("Running Pull Data pipeline in worker...", flush=True)

    if not PULL_DATA_SCRIPT.exists():
        raise FileNotFoundError(f"Could not find {PULL_DATA_SCRIPT}")

    subprocess.run(
        [sys.executable, str(PULL_DATA_SCRIPT)],
        check=True,
        cwd=PULL_DATA_SCRIPT.parent,
    )

    print("Pull Data pipeline complete.", flush=True)


def handle_recompute_analytics():
    """Handle analytics recomputation requests."""
    print(
        "Update analysis requested. Current dashboard queries are dynamic.",
        flush=True,
    )
    print(
        "No materialized summary refresh is needed for this version.",
        flush=True,
    )


def process_task(message):
    """Route one decoded RabbitMQ task message by task kind."""
    task_kind = message.get("kind")
    task_ts = message.get("ts")

    print(f"Received task {task_kind} at {task_ts}", flush=True)

    if task_kind == "scrape_new_data":
        run_pull_data_pipeline()
        return

    if task_kind == "recompute_analytics":
        handle_recompute_analytics()
        return

    raise ValueError(f"Unknown task kind: {task_kind}")


def reject_message(channel, delivery_tag, reason):
    """Reject one RabbitMQ message without requeueing it."""
    print(reason, flush=True)
    channel.basic_nack(
        delivery_tag=delivery_tag,
        requeue=False,
    )


def handle_message(channel, method, properties, body):
    """Decode, process, and acknowledge one RabbitMQ message."""
    del properties

    try:
        message = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        reject_message(
            channel,
            method.delivery_tag,
            f"Invalid JSON task message: {error}",
        )
        return

    try:
        process_task(message)
    except (
        FileNotFoundError,
        OSError,
        subprocess.CalledProcessError,
        ValueError,
    ) as error:
        reject_message(
            channel,
            method.delivery_tag,
            f"Task processing failed: {error}",
        )
        return

    channel.basic_ack(delivery_tag=method.delivery_tag)


def close_connection(connection):
    """Close a RabbitMQ connection if it is still open."""
    if connection is not None and not connection.is_closed:
        connection.close()


def main():
    """Start the RabbitMQ consumer loop."""
    while True:
        connection = None

        try:
            print("Connecting worker to RabbitMQ...", flush=True)
            connection, channel = open_channel()

            print("Worker is waiting for tasks.", flush=True)

            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=handle_message,
            )

            channel.start_consuming()

        except pika.exceptions.AMQPError as error:
            print(
                f"RabbitMQ connection error: {error}. "
                f"Retrying in {RETRY_DELAY_SECONDS} seconds...",
                flush=True,
            )
            time.sleep(RETRY_DELAY_SECONDS)

        finally:
            close_connection(connection)


if __name__ == "__main__":
    main()
