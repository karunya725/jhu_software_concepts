"""RabbitMQ publisher for web-triggered background tasks."""

import json
import os
import uuid
from datetime import datetime, timezone

import pika


RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbit:5672/")
EXCHANGE_NAME = "gradcafe.tasks"
QUEUE_NAME = "tasks"
ROUTING_KEY = "tasks"


def open_channel():
    """Open a RabbitMQ connection and declare the task exchange/queue."""
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
    """Publish a durable task message to RabbitMQ."""
    payload = payload or {}
    headers = headers or {}

    message = {
        "task_id": str(uuid.uuid4()),
        "kind": kind,
        "payload": payload,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    connection, channel = open_channel()

    try:
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=json.dumps(message).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
                headers=headers,
            ),
        )
    finally:
        connection.close()

    return message