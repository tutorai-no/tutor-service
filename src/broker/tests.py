from django.test import TestCase
from broker.producer import producer, KafkaProducerSingleton


# Create your tests here.
class TestProducer(TestCase):
    def test_using_several_producers_are_all_the_same_instance(self):
        kafka_producer_1 = KafkaProducerSingleton().get_producer()
        kafka_producer_2 = KafkaProducerSingleton().get_producer()
        
        self.assertEqual(kafka_producer_1, kafka_producer_2)
        self.assertEqual(producer, kafka_producer_1)

