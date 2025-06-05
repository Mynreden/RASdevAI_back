from datetime import datetime
from typing import Dict, List
import uuid
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

        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.response_consumer_started = False

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

    async def send_message(self, message: dict) -> str:
            """Send message and return correlation ID"""
            await self.connect()
            
            # Generate unique correlation ID
            correlation_id = str(uuid.uuid4())
            
            # Add correlation ID to message
            message_with_id = {**message, "correlation_id": correlation_id}
            
            # Start response consumer if not already started
            if not self.response_consumer_started:
                asyncio.create_task(self._start_response_consumer())
                self.response_consumer_started = True
            
            # Send request
            request_queue = await self.channel.declare_queue(
                self.request_stock_price_queue, 
                durable=True
            )
            
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message_with_id).encode(),
                    correlation_id=correlation_id
                ),
                routing_key=request_queue.name
            )
            
            return correlation_id
        
    async def wait_for_response(self, correlation_id: str, timeout: int = 30) -> List:
        """Wait for response with specific correlation ID"""
        # Create future for this request
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[correlation_id] = future
        
        try:
            # Wait for response
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"No response received within {timeout} seconds")
        finally:
            # Clean up
            self.pending_requests.pop(correlation_id, None)
    
    async def send_message_with_response(self, message: dict, timeout: int = 30) -> List:
        """Send message and wait for correlated response (convenience method)"""
        correlation_id = await self.send_message(message)
        return await self.wait_for_response(correlation_id, timeout)
    
    async def _start_response_consumer(self):
        """Start consuming responses and route them to correct futures"""
        response_queue = await self.channel.declare_queue(
            self.response_stock_price_queue, 
            durable=True
        )
        
        async def on_response(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    correlation_id = message.correlation_id
                    if correlation_id and correlation_id in self.pending_requests:
                        data = json.loads(message.body.decode())
                        future = self.pending_requests[correlation_id]
                        if not future.done():
                            future.set_result(data)
                    else:
                        print(f"⚠️ Received message with unknown correlation_id: {correlation_id}")
                except Exception as e:
                    print(f"❌ Error processing response: {e}")
                    # Try to set exception on future if correlation_id is known
                    correlation_id = getattr(message, 'correlation_id', None)
                    if correlation_id and correlation_id in self.pending_requests:
                        future = self.pending_requests[correlation_id]
                        if not future.done():
                            future.set_exception(e)
        
        await response_queue.consume(on_response)
        print(f"📥 Started response consumer for queue: {self.response_stock_price_queue}")

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
