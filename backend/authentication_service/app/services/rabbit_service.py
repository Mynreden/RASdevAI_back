from datetime import datetime
from typing import List
import aio_pika
import asyncio
import json
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import StockPrice

from ..database import get_db
from ..core import ConfigService, get_config_service

class RabbitService:
    def __init__(self, config_service: ConfigService):
        self.host = config_service.get("RABBIT_HOST")
        self.port = int(config_service.get("RABBIT_PORT"))
        self.username = config_service.get("RABBIT_USERNAME")
        self.password = config_service.get("RABBIT_PASSWORD")

        self.request_stock_price_queue = config_service.get("RABBIT_PORTFOLIO_REQUEST_QUEUE")
        self.response_stock_price_queue = config_service.get("RABBIT_PORTFOLIO_RESPONSE_QUEUE")

        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.Channel | None = None
        self.should_stop = asyncio.Event()
        self.db_service = get_db(config_service)

        self.queue_request_stock_price_name = config_service.get("request_for_the_stock_price")
        self.queue_response_for_the_stock_price_name = config_service.get("response_for_the_stock_price")

    async def connect(self):
        retries = 0
        while retries < 5:
            try:
                self.connection = await aio_pika.connect_robust(
                    host=self.host,
                    port=self.port,
                    login=self.username,
                    password=self.password,
                )
                self.channel = await self.connection.channel()
                print("✅ Connected to RabbitMQ")
                return
            except Exception as e:
                retries += 1
                print(f"❌ RabbitMQ connection failed (retry {retries}): {e}")
                await asyncio.sleep(2 ** retries)

    async def send_message(self, message: dict):
        await self.connect()
        queue = await self.channel.declare_queue(self.request_stock_price_queue, durable=True)
        await self.channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key=queue.name
        )

    async def receive_message(self, timeout: int = 10) -> List[StockPrice]:
        await self.connect()
        queue = await self.channel.declare_queue(self.response_stock_price_queue, durable=True)

        future = asyncio.get_event_loop().create_future()

        async def on_message(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    data = json.loads(message.body.decode())
                    if not future.done():
                        future.set_result(data)
                except Exception as e:
                    if not future.done():
                        future.set_exception(e)

        consumer_tag = await queue.consume(on_message)

        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"No message received from queue '{self.response_stock_price_queue}' within {timeout} seconds"
            )
        finally:
            await queue.cancel(consumer_tag)

    async def stop(self):
        self.should_stop.set()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            print("🔌 RabbitMQ connection closed")

    async def is_healthy(self) -> bool:
        try:
            return self.connection and not self.connection.is_closed
        except Exception:
            return False


def get_rabbit_service(
    config_service: ConfigService = Depends(get_config_service)
) -> RabbitService:
    return RabbitService(config_service)
