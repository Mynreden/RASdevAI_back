import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.handlers import BotHandler
from bot.services import RabbitConsumerService

async def main():
    bot = Bot(token=settings.TELEGRAM_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    bot_handler = BotHandler()
    dp.include_router(bot_handler.router)

    # RabbitMQ consumer
    rabbit_service = RabbitConsumerService(bot)
    rabbit_task = asyncio.create_task(rabbit_service.start_consuming())

    print("🚀 Bot and RabbitMQ started")
    await dp.start_polling(bot)
    await rabbit_task  # если polling завершится

if __name__ == "__main__":
    asyncio.run(main())

