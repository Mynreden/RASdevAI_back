import json
import asyncio
import aio_pika
from aiogram import Bot
from bot.config import settings

class RabbitConsumerService:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.host = settings.RABBIT_HOST
        self.port = settings.RABBIT_PORT
        self.username = settings.RABBIT_USERNAME
        self.password = settings.RABBIT_PASSWORD
        self.queue_name = settings.RABBIT_TELEGRAM_QUEUE
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.Channel | None = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            host=self.host,
            port=self.port,
            login=self.username,
            password=self.password,
        )
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)
        print("✅ Connected to RabbitMQ")

    async def start_consuming(self):
        if not self.connection:
            await self.connect()
        
        queue = await self.channel.declare_queue(self.queue_name, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        data = json.loads(message.body)
                        chat_id = data.get("chat_id")
                        text = data.get("text")
                        if chat_id and text:
                            await self.bot.send_message(chat_id=chat_id, text=text)
                            print(f"📤 Sent message to chat {chat_id}")
                        else:
                            print("❌ Invalid message format:", data)
                    except Exception as e:
                        print(f"❌ Error while processing message: {e}")
