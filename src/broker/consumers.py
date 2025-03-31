import json
import logging
import threading
from typing import Callable
from dataclasses import dataclass
from confluent_kafka import Consumer as KafkaConsumer, KafkaException, KafkaError
from django.conf import settings

from broker.topics import Topic
from broker.handlers.clustering_handler import handle_document_upload_rag
from broker.handlers.activity_handler import (
    handle_activity_streak,
    handle_activity_save,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConsumerConfig:
    topics: list[Topic]
    logic: Callable[[dict], None]
    consumer_group: str = "default"


class Consumer(threading.Thread):
    def __init__(self, config: ConsumerConfig):
        threading.Thread.__init__(self)
        self.settings = settings
        settings.KAFKA_CONFIGURATION["group.id"] = config.consumer_group
        self._consumer = KafkaConsumer(settings.KAFKA_CONFIGURATION)
        self.topics = config.topics
        self.logic = config.logic

    def run(self):
        try:
            # Subcribe to topic
            self._consumer.subscribe([topic.value for topic in self.topics])
            logger.info("Consumer started")

            running = True
            while running:
                # Poll for message
                msg = self._consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                # Handle Error
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        logger.error(
                            f"{msg.topic()}, {msg.partition()}, {msg.offset()} reached end at offset %d\n"
                        )
                elif msg.error():
                    logger.error(f"KafkaException Error occurred: {msg.error()}")
                    raise KafkaException(msg.error())
                else:
                    # Handle Message
                    message = json.loads(msg.value().decode("utf-8"))
                    self.logic(message)
        finally:
            # Close down consumer to commit final offsets.
            self._consumer.close()


CONSUMERS = [
    Consumer(
        ConsumerConfig(
            [Topic.DOCUMENT_UPLOAD_RAG], handle_document_upload_rag, "clustering"
        )
    ),
    Consumer(
        ConsumerConfig([Topic.USER_ACTIVITY], handle_activity_save, "activity_save")
    ),
    Consumer(
        ConsumerConfig([Topic.USER_ACTIVITY], handle_activity_streak, "activity_streak")
    ),
]


def start_consumers():

    for consumer in CONSUMERS:
        consumer.start()
