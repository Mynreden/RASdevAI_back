import asyncio
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import aio_pika
from fastapi import Depends
from ..core import ConfigService, get_config_service
from ..schemas import EmailToSend


class EmailService:
    def __init__(self, config_service):
        self.email_queue = config_service.get("RABBIT_EMAIL_QUEUE")
        self.host = config_service.get("RABBIT_HOST")
        self.port = int(config_service.get("RABBIT_PORT"))
        self.username = config_service.get("RABBIT_USERNAME")
        self.password = config_service.get("RABBIT_PASSWORD")
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.Channel | None = None
        self.should_stop = asyncio.Event()

    async def connect(self):
        retries = 0
        while retries < 5:
            try:
                self.connection = await aio_pika.connect_robust(
                    host=self.host,
                    port=self.port,
                    login=self.username,
                    password=self.password
                )                
                self.channel = await self.connection.channel()
                await self.channel.declare_queue(
                    self.email_queue,
                    durable=True  # очередь сохранится даже при перезапуске брокера
                )
                print("✅ Connected to RabbitMQ")
                return
            except Exception as e:
                retries += 1
                print(f"❌ RabbitMQ connection failed (retry {retries}): {e}")
                await asyncio.sleep(2 ** retries)

    async def close(self):
        if self.connection:
            await self.connection.close()

    async def send_email(self, email_data: EmailToSend):
        if self.channel is None:
            raise RuntimeError("❌ RabbitMQ channel is not initialized. Call connect() first.")
        try:
            message_body = email_data.model_dump_json().encode()
            print(message_body)
            message = aio_pika.Message(
                body=message_body,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await self.channel.default_exchange.publish(
                message,
                routing_key=self.email_queue
            )
        except Exception as ex:
            print(ex)

        print(f"✅ Email message sent to queue {self.email_queue} for {email_data.email}")

    async def send_verification_email(self, to_email: str, verification_link: str):
        subject = "Verify Your Email Address"
        text_content = f"""\
        Hi,

        Thank you for registering. Please verify your email address by clicking on the link below:
        {verification_link}

        If you did not register, please ignore this email.
        """
        html_content = f"""\
        <html>
        <body>
            <p>Hi,</p>
            <p>Thank you for registering. Please verify your email address by clicking on the link below:</p>
            <p><a href="{verification_link}">Verify Email</a></p>
            <p>If you did not register, please ignore this email.</p>
        </body>
        </html>
        """
        email = EmailToSend(email=to_email,
            subject=subject,
            body=text_content)
        await self.send_email(email)

email_service_singleton: EmailService | None = None

def get_email_service(config_service: ConfigService = Depends(get_config_service)) -> EmailService:
    global email_service_singleton
    if email_service_singleton is None:
        email_service_singleton = EmailService(config_service)
    return email_service_singleton
