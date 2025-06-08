from aio_pika import IncomingMessage
from fastapi import Depends
import json
from sqlalchemy import select
from ..schemas import StocksFromRabbit
from .email_service import get_email_service, EmailService
from .telegram_service import get_telegram_service, TelegramService
from .rabbit_manager import get_rabbit_manager, RabbitMQManager
from ..core import get_config_service, ConfigService
from ..database import get_db_service, DBService
from ..models import AlertItem, User

class ConsumerService:
    def __init__(
        self,
        rabbit_manager: RabbitMQManager,
        email_service: EmailService,
        telegram_service: TelegramService,
        queue_name: str,
        db_service: DBService
    ):
        self.rabbit_manager = rabbit_manager
        self.email_service = email_service
        self.telegram_service = telegram_service
        self.queue_name = queue_name
        self.db_service = db_service
        self._task = None

    async def start(self):
        channel = await self.rabbit_manager.get_channel()
        queue = await channel.declare_queue(self.queue_name, durable=True)
        await queue.consume(self.process_queue_message)
        print(f"🎧 Consuming queue: {self.queue_name}")

    async def process_queue_message(self, message: IncomingMessage):
        async with message.process():
            try:
                payload = json.loads(message.body)
                data = StocksFromRabbit(**payload)

                print(f"✅ Received message: {data.ticker} {data.close} at {data.date}")

                async with self.db_service.async_session_maker() as session:
                    alerts = await session.execute(
                        select(AlertItem).where(AlertItem.stock_symbol == data.ticker)
                    )
                    alert_items = alerts.scalars().all()

                    for alert in alert_items:
                        should_alert = False
                        if alert.more_than is not None and data.close > alert.more_than:
                            should_alert = True
                        elif alert.less_than is not None and data.close < alert.less_than:
                            should_alert = True

                        if should_alert:
                            condition = ""
                            if alert.more_than is not None and data.close > alert.more_than:
                                condition = f"превысила порог {alert.more_than}"
                            elif alert.less_than is not None and data.close < alert.less_than:
                                condition = f"опустилась ниже порога {alert.less_than}"
                            user:User = (await session.execute(
                                select(User).where(User.id == alert.user_id)
                            )).scalar()
                            if user:
                                message_text = (
                                    f"📢 Уведомление для пользователя {user.username}:\n\n"
                                    f"📊 Акция {data.ticker} на дату {data.date} имеет цену {data.close}.\n"
                                    f"🔔 Она {condition}.\n"
                                    f"🧾 Ваше условие сработало.\n\n"
                                    f"Подробности смотрите на сайте https://rasdevai.vercel.app/"
                                )
                                await self.send_alerts(user, message_text)
                            else:
                                print(f"❌ User not found for ID {alert.user_id}")

                print(f"✅ Processed and checked alerts for {data.ticker}")

            except Exception as e:
                print(f"❌ Failed to process message from {self.queue_name}: {e}")

    async def send_alerts(self, user: User, message: str):
        try:
            await self.email_service.send_alert(user.email, subject="Stock Alert", body=message)
            if user.telegram_id:
                await self.telegram_service.send_alert(user.telegram_id, message)
            print(f"📤 Alert sent to user {user.email}")
        except Exception as e:
            print(f"❌ Failed to send alert to user {user.email}: {e}")


    async def run(self):
        await self.start()

    async def stop(self):
        await self.rabbit_manager.close()


consumer_service_singleton: ConsumerService | None = None

def get_consumer_service(
    rabbit_manager: RabbitMQManager = Depends(get_rabbit_manager),
    email_service: EmailService = Depends(get_email_service),
    telegram_service: TelegramService = Depends(get_telegram_service),
    config_service: ConfigService = Depends(get_config_service),
    db_service: DBService = Depends(get_db_service)
) -> ConsumerService:
    global consumer_service_singleton
    if consumer_service_singleton is None:
        consumer_service_singleton = ConsumerService(
            rabbit_manager=rabbit_manager,
            email_service=email_service,
            telegram_service=telegram_service,
            queue_name=config_service.get("RABBIT_STOCKS_QUEUE_ALERT"),
            db_service=db_service
        )
    return consumer_service_singleton
