import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from aiokafka import AIOKafkaConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.consumer import routers as kafka_routers
from src.consumer.service import consume_single_users, consume_single_orders
from src.config import KafkaConfig

config = KafkaConfig()


async def start_consumers():
    """Запуск Kafka Consumer"""
    kafka_consumer_users = AIOKafkaConsumer(
            config.KAFKA_TOPIC_USERS,
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            group_id=config.GROUP_ID,
            enable_auto_commit=True,
        )
    await kafka_consumer_users.start()

    kafka_consumer_orders = AIOKafkaConsumer(
            config.KAFKA_TOPIC_ORDERS,
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            group_id=config.GROUP_ID,
            enable_auto_commit=True,
        )
    await kafka_consumer_orders.start()

    return dict(users=kafka_consumer_users, orders=kafka_consumer_orders)


async def shutdown_consumer(kafka_consumer: AIOKafkaConsumer):
    """Остановка Kafka Consumer"""
    await kafka_consumer.stop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Добавление kafka consumer в объект FastApi, чтобы не запускать consumer при каждом запросе"""
    app.kafka_consumers = await start_consumers()
    app.scheduler = AsyncIOScheduler()
    app.scheduler.add_job(
        consume_single_users, 
        args=(app, config),
        trigger=IntervalTrigger(seconds=config.POLL_INTERVAL_SECONDS),
        id='poll_kafka_users',
        replace_existing=False
    )
    app.scheduler.add_job(
        consume_single_orders, 
        args=(app, config),
        trigger=IntervalTrigger(seconds=config.POLL_INTERVAL_SECONDS),
        id='poll_kafka_orders',
        replace_existing=False
    )
    app.scheduler.start()
    app.schema_client = SchemaRegistryClient(dict(url=config.SCHEMA_REGISTRY_SERVER))
    app.include_router(kafka_routers.all_routers)
    yield
    await shutdown_consumer(app.kafka_consumer['users'])
    await shutdown_consumer(app.kafka_consumer['orders'])
    app.scheduler.shutdown()

app = FastAPI(
    title="Kafka consumer",
    description="""
            Получает сообщения из Kafka
            """,
    version="1.0.0",
    lifespan=lifespan
)

async def start_fastapi():
    """Запуск FastAPI сервера"""
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=9001,
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Основная точка входа - запуск веб-сервера Uvicorn
    """
    await asyncio.create_task(
        start_fastapi(),
    )


if __name__ == "__main__":
    asyncio.run(main())
