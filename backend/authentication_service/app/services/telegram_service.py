from aio_pika import Message, DeliveryMode
from fastapi import Depends
from ..schemas import TelegramToSend
from .rabbit_manager import RabbitMQManager, get_rabbit_manager
from ..core import ConfigService, get_config_service

class TelegramService:
    def __init__(self, rabbit_manager: RabbitMQManager, queue_name: str):
        self.rabbit_manager = rabbit_manager
        self.queue_name = queue_name

    async def send_message(self, telegram: TelegramToSend):
        channel = await self.rabbit_manager.get_channel()
        await channel.default_exchange.publish(
            Message(
                body=telegram.model_dump_json().encode(),
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT
            ),
            routing_key=self.queue_name
        )
        print(f"📤 Telegram message sent to queue '{self.queue_name}'")

    async def send_alert(self, telegram_id: int, text: int):
        await self.send_message(TelegramToSend(chat_id=telegram_id, text=text))


telegram_service_singleton: TelegramService | None = None

def get_telegram_service(rabbit_manager: RabbitMQManager = Depends(get_rabbit_manager), 
                      config_service: ConfigService = Depends(get_config_service)) -> TelegramService:
    global telegram_service_singleton
    if telegram_service_singleton is None:
        telegram_service_singleton = TelegramService(rabbit_manager, config_service.get("RABBIT_TELEGRAM_QUEUE"))
    return telegram_service_singleton