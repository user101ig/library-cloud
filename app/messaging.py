"""Αποστολή domain events στο RabbitMQ."""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime

import pika

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://library:library@localhost:5672/")
EVENT_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "library.events")


def publish_event(event_type: str, data: dict[str, str]) -> bool:
    # Το API συνεχίζει να λειτουργεί ακόμη κι αν το RabbitMQ είναι προσωρινά εκτός.
    event = {
        "type": event_type,
        "occurred_at": datetime.now(UTC).isoformat(),
        "data": data,
    }
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.exchange_declare(exchange=EVENT_EXCHANGE, exchange_type="topic", durable=True)
        channel.basic_publish(
            exchange=EVENT_EXCHANGE,
            routing_key=event_type,
            body=json.dumps(event).encode(),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=pika.DeliveryMode.Persistent,
            ),
        )
        connection.close()
        return True
    except pika.exceptions.AMQPError:
        logger.exception("Could not publish RabbitMQ event %s", event_type)
        return False
