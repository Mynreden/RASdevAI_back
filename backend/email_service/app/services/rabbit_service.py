import aio_pika
import asyncio
import json
from fastapi import Depends
from ..schemas import EmailToSend
from .email_sender import EmailSenderService
from ..core import ConfigService, get_config_service


class RabbitService:
    def __init__(self, config_service: ConfigService, email_sender: EmailSenderService):
        self.host = config_service.get("RABBIT_HOST")
        self.port = int(config_service.get("RABBIT_PORT"))
        self.password = config_service.get("RABBIT_USERNAME")
        self.username = config_service.get("RABBIT_PASSWORD")
        self.email_queue = config_service.get("RABBIT_EMAIL_QUEUE")
        self.email_sender = email_sender
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.Channel | None = None
        self.should_stop = asyncio.Event()

    async def connect(self):
        retries = 0
        while retries < 5:
            try:
                self.connection = await aio_pika.connect_robust(host=self.host, port=self.port, password=self.password)
                self.channel = await self.connection.channel()
                print("✅ Connected to RabbitMQ")
                return
            except Exception as e:
                retries += 1
                print(f"❌ RabbitMQ connection failed (retry {retries}): {e}")
                await asyncio.sleep(2 ** retries)

    async def start_consumer(self):
        await self.connect()
        queue = await self.channel.declare_queue(self.email_queue, durable=True)

        async def on_message(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    data = json.loads(message.body)
                    email_data = EmailToSend(**data)
                    print(email_data)
                    await self.email_sender.send_email(
                        email_data
                    )
                    print(f"📤 Sent email to {email_data.email}")
                except Exception as e:
                    print(f"❌ Failed to send email: {e}")

        await queue.consume(on_message)
        print("📥 Email consumer started.")

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


# DI
def get_rabbit_service(
    config_service: ConfigService = Depends(get_config_service),
    email_sender_service: EmailSenderService = Depends(EmailSenderService),
) -> RabbitService:
    return RabbitService(config_service, email_sender_service)
