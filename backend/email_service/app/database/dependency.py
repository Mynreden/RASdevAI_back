from .db_service import DBService, get_db_service
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import AsyncGenerator

async def get_db(db_service: DBService = Depends(get_db_service)) -> AsyncGenerator[AsyncSession, None]:
    async for session in db_service.get_db():
        yield session
