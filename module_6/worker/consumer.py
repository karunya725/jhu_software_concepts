"""RabbitMQ consumer for Grad Cafe background tasks."""

import json
import os
import time
import pika
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PULL_DATA_SCRIPT = BASE_DIR / "module_2_code" / "pull_new_data.py"


RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbit:5672/")

EXCHANGE_NAME = "tasks"
QUEUE_NAME = "tasks_q"
ROUTING_KEY = "tasks"


def open_channel():
    """Open RabbitMQ connection and declare durable task infrastructure."""
    parameters = pika.URLParameters(RABBITMQ_URL)
    parameters.heartbeat = 1800
    parameters.blocked_connection_timeout = 1800
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type="direct",
        durable=True,
    )

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True,
    )

    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=QUEUE_NAME,
        routing_key=ROUTING_KEY,
    )

    channel.basic_qos(prefetch_count=1)

    return connection, channel


def process_task(message):
    """Process one task message."""
    task_kind = message.get("kind")
    task_ts = message.get("ts")
    
    print(f"Received task {task_kind} at {task_ts}", flush=True)

    if task_kind == "scrape_new_data":
        print("Running Pull Data pipeline in worker...", flush=True)

        if not PULL_DATA_SCRIPT.exists():
            raise FileNotFoundError(f"Could not find {PULL_DATA_SCRIPT}")

        subprocess.run(
            [sys.executable, str(PULL_DATA_SCRIPT)],
            check=True,
            cwd=PULL_DATA_SCRIPT.parent,
        )

        print("Pull Data pipeline complete.", flush=True)
        return

    if task_kind == "recompute_analytics":
        print("Update analysis requested. Current dashboard queries are dynamic.", flush=True)
        print("No materialized summary refresh is needed for this version.", flush=True)
        return

    print(f"Unknown task kind: {task_kind}", flush=True)


def handle_message(channel, method, properties, body):
    """Decode, process, and acknowledge one RabbitMQ message."""
    del properties

    try:
        message = json.loads(body.decode("utf-8"))
        process_task(message)
        channel.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as error:  # pylint: disable=broad-exception-caught
        print(f"Task failed: {error}", flush=True)
        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False,
        )


def main():
    """Start the RabbitMQ consumer loop."""
    while True:
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
            print(f"RabbitMQ connection error: {error}. Retrying in 5 seconds...", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()