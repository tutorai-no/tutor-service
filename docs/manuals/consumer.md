# Consumer

A consumer can listen in on a Kafka topic and will procces incomming messages. To create a new consumer, do the following:

In `src/broker/consumer.py` add a new consummer in the following snippet:

```python
CONSUMERS = [
    Consumer(ConsumerConfig([Topic.DOCUMENT_UPLOAD_RAG], handle_document_upload_rag)),
]
```

The `CONSUMERS` list contains all the consumers that will be started when the broker is started. The `Consumer` class takes two arguments, a `ConsumerConfig` object and a function that will be called when a message is received.

All consumer functions should be defined in `src/broker/handlers/` directory. Handler functions are then defined in their topic specific file. For example, the `handle_activity_streak` function is defined in `src/broker/handlers/activity_handlers.py`. In addition, in the topic specific file, a Pydantic object should be defined that represents the message that is expected to be received by the consumer. For example, the `ActivityMessage` object is defined in `src/broker/handlers/activity_handlers.py`.

## Testing

All consumers must be tested. To test a consumer, test the handler function that is called when a message is received. The handler function should be tested with a message that is expected to be received by the consumer. To see an example of how to test a consumer, see the `HandleActivityMessageTests` function in `src/learning_materials/tests/test_kafka.py`:



