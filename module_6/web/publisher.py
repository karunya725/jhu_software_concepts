"""RabbitMQ publisher for web-triggered background tasks."""

import json
import os
from datetime import datetime, timezone

import pika


RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbit:5672/")

EXCHANGE_NAME = "tasks"
QUEUE_NAME = "tasks_q"
ROUTING_KEY = "tasks"


def _open_channel():
    """Open RabbitMQ connection and declare durable task infrastructure."""
    parameters = pika.URLParameters(RABBITMQ_URL)
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

    return connection, channel


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