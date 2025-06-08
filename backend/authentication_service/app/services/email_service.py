from aio_pika import Message, DeliveryMode
from fastapi import Depends
from ..schemas import EmailToSend
from .rabbit_manager import RabbitMQManager, get_rabbit_manager
from ..core import get_config_service, ConfigService

class EmailService:
    def __init__(self, rabbit_manager: RabbitMQManager, queue_name: str):
        self.rabbit_manager = rabbit_manager
        self.queue_name = queue_name

    async def send_email(self, email_data: EmailToSend):
        channel = await self.rabbit_manager.get_channel()
        if channel is None:
            raise RuntimeError("❌ RabbitMQ channel is not initialized. Call connect() first.")
        try:
            message_body = email_data.model_dump_json().encode()
            print(message_body)
            message = Message(
                body=message_body,
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT
            )
            await channel.default_exchange.publish(
                message,
                routing_key=self.queue_name
            )
        except Exception as ex:
            print(ex)

        print(f"✅ Email message sent to queue {self.queue_name} for {email_data.email}")

    async def send_alert(self, to_email: str, subject: str, body: str):
        email = EmailToSend(email=to_email,
            subject=subject,
            body=body)
        await self.send_email(email)

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

def get_email_service(rabbit_manager: RabbitMQManager = Depends(get_rabbit_manager), 
                      config_service: ConfigService = Depends(get_config_service)) -> EmailService:
    global email_service_singleton
    if email_service_singleton is None:
        email_service_singleton = EmailService(rabbit_manager, config_service.get("RABBIT_EMAIL_QUEUE"))
    return email_service_singleton
