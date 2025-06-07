import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.services.db_service import DBService
from bot.config import settings
from bot.handlers import register_handlers, router  # <-- твой модуль с register_handlers

async def main():
    bot = Bot(token=settings.TELEGRAM_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    db_service = DBService(settings.DATABASE_URL)  # Получаем инстанс
    register_handlers(router, db_service)
    dp.include_router(router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
