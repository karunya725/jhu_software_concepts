"""RabbitMQ publisher for web-triggered background tasks."""

import json
import os
from datetime import datetime, timezone

import pika

from shared.rabbitmq_helpers import open_task_channel


RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbit:5672/")

EXCHANGE_NAME = "tasks"
QUEUE_NAME = "tasks_q"
ROUTING_KEY = "tasks"


def _open_channel():
    """Open RabbitMQ connection and declare durable task infrastructure."""
    return open_task_channel(
        RABBITMQ_URL,
        EXCHANGE_NAME,
        QUEUE_NAME,
        ROUTING_KEY,
    )


def publish_task(kind, payload=None, headers=None):
    """Publish a durable JSON task message to RabbitMQ."""
    payload = payload or {}
    headers = headers or {}

    body = json.dumps(
        {
            "kind": kind,
            "ts": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        },
        separators=(",", ":"),
    ).encode("utf-8")

    connection, channel = _open_channel()

    try:
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
                headers=headers,
            ),
            mandatory=False,
        )
    finally:
        connection.close()
