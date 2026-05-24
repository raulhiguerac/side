import os
import uuid
import json
import base64
from functools import partial
from typing import Callable

from pydantic import ValidationError
from confluent_kafka import Consumer, Producer

from app.core.exceptions.worker import WorkerConfigurationError, WorkerDeliveryError
from app.core.logging.logger import get_logger
from app.services.prediction.use_cases.batch import BatchPrediction
from app.workers.listing_created.helpers.types import WorkerMessage

logger = get_logger(__name__)

_ENV_VARS = (
    'KAFKA_SERVER',
    'KAFKA_GROUP_ID',
    'KAFKA_TOPIC',
    'KAFKA_PREDICTIONS_TOPIC',
    'KAFKA_DLQ_TOPIC',
)


class ListingConsumer:
    def __init__(self, uc: BatchPrediction) -> None:
        env = {k: os.getenv(k) for k in _ENV_VARS}
        missing = [k for k, v in env.items() if not v]
        if missing:
            raise WorkerConfigurationError(missing=missing)

        server_principal = os.getenv('WORKER_PRINCIPAL')

        consumer = Consumer({
            'bootstrap.servers': env['KAFKA_SERVER'],
            'group.id': env['KAFKA_GROUP_ID'],
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        })

        producer = Producer({'bootstrap.servers': env['KAFKA_SERVER']})

        consumer.subscribe([env['KAFKA_TOPIC']])

        self.uc = uc
        self.consumer = consumer
        self.producer = producer
        self.principal = server_principal
        self.topic = env['KAFKA_TOPIC']
        self.topic_predictions = env['KAFKA_PREDICTIONS_TOPIC']
        self.topic_dlq = env['KAFKA_DLQ_TOPIC']

    def close(self) -> None:
        self.consumer.close()

    def __enter__(self):
        return self

    def __exit__(self, *_) -> None:
        self.close()

    @staticmethod
    def delivery_report(err, msg) -> None:
        if err is not None:
            logger.error("delivery_failed", extra={"error": str(err), "topic": msg.topic()})

    @staticmethod
    def serialize(messages: list) -> list[str]:
        def _default(obj):
            if isinstance(obj, uuid.UUID):
                return str(obj)
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            raise TypeError(f"{type(obj)} is not serializable")
        return [json.dumps(msg, default=_default) for msg in messages]

    @staticmethod
    def produce(producer: Producer, topic: str, messages: list[str], callback: Callable) -> None:
        delivery_errors: list[str] = []

        def _delivery_report(err, msg) -> None:
            callback(err, msg)
            if err is not None:
                delivery_errors.append(str(err))

        for msg in messages:
            producer.produce(topic, value=msg.encode("utf-8"), on_delivery=_delivery_report)

        pending = producer.flush()
        if pending or delivery_errors:
            raise WorkerDeliveryError(topic=topic, errors=delivery_errors, pending=pending)

    def _poll_batch(self) -> tuple[list[str], list[str]]:
        messages = []
        rejected_messages = []

        while True:
            msg = self.consumer.poll(1.0)
            if msg is None:
                break
            if msg.error():
                logger.error(
                    "kafka_message_error",
                    extra={"error": str(msg.error())}
                )
                continue
            try:
                messages.append(msg.value().decode("utf-8"))
            except UnicodeDecodeError as exc:
                logger.error("message_decode_failed", exc_info=exc)
                raw_value = msg.value() or b""
                rejected_messages.append(json.dumps({
                    "reason": "MESSAGE_DECODE_FAILED",
                    "encoding": "base64",
                    "value": base64.b64encode(raw_value).decode("ascii"),
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "offset": msg.offset(),
                }))
        return messages, rejected_messages

    async def consume_batch(self) -> None:
        valid_messages: dict[uuid.UUID, WorkerMessage] = {}
        dlq: list[str] = []
        _emit = partial(self.produce, producer=self.producer, callback=self.delivery_report)

        raw_messages, rejected_messages = self._poll_batch()

        if rejected_messages:
            dlq.extend(rejected_messages)

        if not raw_messages and not rejected_messages:
            return

        for raw in raw_messages:
            try:
                data = json.loads(raw)
                message = WorkerMessage.model_validate(data)
            except (json.JSONDecodeError, ValidationError):
                dlq.append(raw)
                continue

            if message.attempts > 3:
                dlq.append(raw)
                continue

            valid_messages[message.id] = message

        domain_messages = [
            (msg.id, msg.model)
            for msg in valid_messages.values()
        ]

        if not domain_messages:
            if dlq:
                _emit(topic=self.topic_dlq, messages=dlq)
            self.consumer.commit()
            return

        result = await self.uc.execute(principal=self.principal,messages=domain_messages)

        # predictions
        if result.predictions:
            _emit(
                topic=self.topic_predictions,
                messages=self.serialize(result.predictions)
            )

        # retries
        if result.failed:
            retry_messages = []

            for msg_id, req in result.failed:
                msg = valid_messages.get(msg_id)
                if not msg:
                    logger.error("retry_message_not_found", extra={"id": str(msg_id)})
                    continue
                retry_messages.append({
                    "id": str(msg_id),
                    "attempts": msg.attempts + 1,
                    "model": req,
                })

            if retry_messages:
                _emit(
                    topic=self.topic,
                    messages=self.serialize(retry_messages)
                )

        # DLQ
        if dlq:
            _emit(topic=self.topic_dlq,messages=dlq)

        # commit offsets
        self.consumer.commit()
