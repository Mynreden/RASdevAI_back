from datetime import datetime
import aio_pika
import asyncio
import json
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from ..models import News, StockPrice, Company, FinancialData

from ..schemas import NewsFromRabbit, StocksFromRabbit, FinancialDataFromRabbit
from ..database import get_db_service
from ..core import ConfigService, get_config_service

class RabbitService:
    def __init__(self, config_service: ConfigService):
        self.host = config_service.get("RABBIT_HOST")
        self.port = int(config_service.get("RABBIT_PORT"))
        self.username = config_service.get("RABBIT_USERNAME")
        self.password = config_service.get("RABBIT_PASSWORD")
        self.queue1_name = config_service.get("RABBIT_NEWS_QUEUE")
        self.queue2_name = config_service.get("RABBIT_STOCKS_QUEUE")
        self.queue3_name = config_service.get("RABBIT_FINANCIAL_QUEUE")

        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.Channel | None = None
        self.should_stop = asyncio.Event()
        self.db_service = get_db_service(config_service)

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

    # async def process_queue1_message(self, message: aio_pika.IncomingMessage):
    #     # async with message.process():
    #         try:
    #             payload = json.loads(message.body)
    #             data = NewsFromRabbit(**payload)
    #             async with self.db_service.async_session_maker() as session:
    #                 news = News(
    #                     ticker=data.ticker,
    #                     date=datetime.fromisoformat(data.create_datetime),  # преобразуем ISO-строку в datetime
    #                     title=data.subject,
    #                     content=data.body,
    #                     source="KASE",  # или другой источник, если есть
    #                     important=data.is_important,
    #                     neutral=data.sentiment_probs.neutral,
    #                     positive=data.sentiment_probs.positive,
    #                     negative=data.sentiment_probs.negative,
    #                 )
    #                 session.add(news)
    #                 #await session.commit()
    #             print(f"✅ Processed message from {self.queue1_name}")
    #         except Exception as e:
    #             print(f"❌ Failed to process message from {self.queue1_name}: {e}")

    async def process_queue2_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                payload = json.loads(message.body)
                data = StocksFromRabbit(**payload)
                async with self.db_service.async_session_maker() as session:
                    company = await session.scalar(
                        select(Company).where(Company.ticker == data.ticker)
                    )

                    if not company:
                        print(f"⚠️ Company with ticker {data.ticker} not found")
                        price = StockPrice(
                            date=data.date,
                            open=data.open,
                            high=data.high,
                            low=data.low,
                            close=data.close,
                            volume=data.volume,
                            company_id=None,
                            ticker=data.ticker
                        )
                    else:
                        price = StockPrice(
                            date=data.date,
                            open=data.open,
                            high=data.high,
                            low=data.low,
                            close=data.close,
                            volume=data.volume,
                            company_id=company.id,
                            ticker=data.ticker
                        )
                    session.add(price)
                    await session.commit()
                print(f"✅ Processed message from {self.queue2_name}")
            except Exception as e:
                print(f"❌ Failed to process message from {self.queue2_name}: {e}")

    async def process_queue3_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                payload = json.loads(message.body)
                data = FinancialDataFromRabbit(**payload)

                async with self.db_service.async_session_maker() as session:
                    record = FinancialData(
                        ticker=data.ticker,
                        change_date=data.change_date,
                        units=data.units,
                        currency=data.currency,
                        net_profit=data.net_profit,
                        own_capital=data.own_capital,
                        aggregate_assets=data.aggregate_assets,
                        authorized_capital=data.authorized_capital,
                        common_book_value=data.common_book_value,
                        total_liabilities=data.total_liabilities,
                        roe=data.roe,
                        roa=data.roa,
                    )
                    session.add(record)
                    await session.commit()
                print(f"✅ Processed message from {self.queue3_name}")
            except Exception as e:
                print(f"❌ Failed to process message from {self.queue3_name}: {e}")

    async def start_consumers(self):
        await self.connect()
        await self.channel.set_qos(prefetch_count=10)

        # queue1 = await self.channel.declare_queue(self.queue1_name, durable=True)
        # queue2 = await self.channel.declare_queue(self.queue2_name, durable=True)
        queue3 = await self.channel.declare_queue(self.queue3_name, durable=True)

        # await queue1.consume(self.process_queue1_message)
        # await queue2.consume(self.process_queue2_message)
        await queue3.consume(self.process_queue3_message)

        print(f"📥 Consumers started for queues: {self.queue1_name}, {self.queue2_name}, {self.queue3_name}")

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


# DI provider для FastAPI
def get_rabbit_service(
    config_service: ConfigService = Depends(get_config_service)
) -> RabbitService:
    return RabbitService(config_service)
