import json

from loguru import logger
from fastapi import FastAPI
from aiokafka.structs import ConsumerRecord
from confluent_kafka.schema_registry.avro import AvroDeserializer, SerializationContext

from src.config import KafkaConfig


async def process_message(app: FastAPI, config: KafkaConfig, msg: ConsumerRecord, topic: str):
    deserializer = AvroDeserializer(app.schema_client)
    context_key = SerializationContext(topic, topic + '-key')
    context_value = SerializationContext(topic, topic + '-value')

    logger.info(json.dumps(dict(
        topic=msg.topic,
        partition=msg.partition,
        offset=msg.offset,
        key=deserializer(msg.key, context_key),
        message=deserializer(msg.value, context_value),
        timestamp=msg.timestamp
    )))


async def consume_single_users(app: FastAPI, config: KafkaConfig):
    result = await app.kafka_consumers['users'].getone()
    await process_message(app, config, result, config.KAFKA_TOPIC_USERS)


async def consume_single_orders(app: FastAPI, config: KafkaConfig):
    result = await app.kafka_consumers['orders'].getone()
    await process_message(app, config, result, config.KAFKA_TOPIC_ORDERS)
