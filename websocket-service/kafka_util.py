import threading
import json
import time
from kafka import KafkaProducer, KafkaConsumer
from loguru import logger
from kafka.errors import NoBrokersAvailable
from kafka.admin import KafkaAdminClient, NewTopic

BOOTSTRAP_SERVERS = 'kafka:9092'
OUTBOUND_TOPIC_NAME = 'new_message'
INBOUND_TOPIC_NAME = 'persisted_message'


def create_topic():
    while True:
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=BOOTSTRAP_SERVERS,
                client_id='ws_admin'
            )
            break
        except:
            logger.exception(f'Could not connect to Kafka at {BOOTSTRAP_SERVERS}')
            time.sleep(1)

    topic_list = [NewTopic(name=OUTBOUND_TOPIC_NAME, num_partitions=1, replication_factor=1)]
    logger.info(admin_client.list_topics())
    admin_client.create_topics(new_topics=topic_list, validate_only=False)
    logger.info(f'Created topic: {OUTBOUND_TOPIC_NAME}')


def create_producer():
    return KafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS, value_serializer=json_serializer)


def create_consumer():
    consumer = KafkaConsumer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        # auto_offset_reset='earliest',
        # consumer_timeout_ms=1000
    )
    consumer.subscribe([INBOUND_TOPIC_NAME])
    logger.info(f"Created consumer {INBOUND_TOPIC_NAME!r}")
    return consumer


def json_serializer(data):
    return json.dumps(data).encode("utf-8")
