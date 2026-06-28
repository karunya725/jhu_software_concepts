"""Shared RabbitMQ helper functions for Module 6 services."""

import pika


def open_task_channel(rabbitmq_url, exchange_name, queue_name, routing_key):
    """Open RabbitMQ connection and declare durable task infrastructure."""
    parameters = pika.URLParameters(rabbitmq_url)
    parameters.heartbeat = 1800
    parameters.blocked_connection_timeout = 1800

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.exchange_declare(
        exchange=exchange_name,
        exchange_type="direct",
        durable=True,
    )

    channel.queue_declare(
        queue=queue_name,
        durable=True,
    )

    channel.queue_bind(
        exchange=exchange_name,
        queue=queue_name,
        routing_key=routing_key,
    )

    return connection, channel
