from .db_service import DBService, get_db_service
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import AsyncGenerator

async def get_db(db_service: DBService = Depends(get_db_service)) -> AsyncGenerator[AsyncSession, None]:
    try:
        async for session in db_service.get_db():
            yield session
    except Exception as e:
        print(f"❌ Ошибка при получении сессии БД: {e}")
        raise  # или можно вернуть HTTPException(status_code=500, detail="DB error")