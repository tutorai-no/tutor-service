import threading
from confluent_kafka import Producer
from django.conf import settings
import logging


logger = logging.getLogger(__name__)


class KafkaProducerSingleton:
    _instance: Producer = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._producer = Producer(settings.KAFKA_CONFIGURATION)
        return cls._instance

    def get_producer(self) -> Producer:
        return self._producer


producer = KafkaProducerSingleton().get_producer()
