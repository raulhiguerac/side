import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.listing_created.consumer import ListingConsumer

PRINCIPAL = uuid.uuid4()
PROP_ID = uuid.uuid4()

_ENV = {
    "KAFKA_SERVER": "localhost:9092",
    "KAFKA_GROUP_ID": "test-group",
    "KAFKA_TOPIC": "listing-created",
    "KAFKA_PREDICTIONS_TOPIC": "price-predicted",
    "KAFKA_DLQ_TOPIC": "listing-created-dlq",
    "WORKER_PRINCIPAL": str(PRINCIPAL),
}

VALID_MODEL_DICT = {
    "area_m2": 80.0,
    "bedrooms": 2,
    "bathrooms": 1.0,
    "parking_spots": 1,
    "stratum": 4,
    "property_type": "apartment",
    "lat": 4.65,
    "lon": -74.05,
    "barrio_ideca": "CHAPINERO",
}

VALID_MSG = json.dumps({"id": str(PROP_ID), "attempts": 1, "model": VALID_MODEL_DICT})


def make_consumer(monkeypatch, uc=None, env_overrides=None):
    env = {**_ENV, **(env_overrides or {})}
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    if uc is None:
        uc = AsyncMock()
    with (
        patch("app.workers.listing_created.consumer.Consumer"),
        patch("app.workers.listing_created.consumer.Producer"),
    ):
        c = ListingConsumer(uc=uc)
    c.producer.flush.return_value = 0
    return c, uc


def poll_seq(consumer, *msgs):
    """Set poll side_effect: provided messages in order, then None to end the loop."""
    consumer.consumer.poll.side_effect = list(msgs) + [None]


def good_msg(data: str):
    msg = MagicMock()
    msg.error.return_value = None
    msg.value.return_value = data.encode("utf-8")
    msg.topic.return_value = "listing-created"
    msg.partition.return_value = 0
    msg.offset.return_value = 0
    return msg


def bad_utf8_msg():
    msg = MagicMock()
    msg.error.return_value = None
    msg.value.return_value = b"\xff\xfe"
    msg.topic.return_value = "listing-created"
    msg.partition.return_value = 0
    msg.offset.return_value = 0
    return msg


def error_msg():
    msg = MagicMock()
    msg.error.return_value = "kafka partition error"
    return msg
