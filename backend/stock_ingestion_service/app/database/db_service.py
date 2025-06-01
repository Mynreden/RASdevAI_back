# db_service.py
from functools import lru_cache
import uuid
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
from fastapi import Depends
from ..core import ConfigService, get_config_service

class DBService:
    def __init__(self, config : ConfigService):
        database_url = config.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL is not set in config!")

        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=15,
            max_overflow=20,
            pool_timeout=30,
            connect_args={"statement_cache_size": 0},
            #poolclass=NullPool  # 🔑 Важно: без пула
            #pool_pre_ping=True,  
        )

        self.async_session_maker = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.async_session_maker() as session:
            yield session

    async def init_db(self, base_model):
        async with self.engine.begin() as conn:
            await conn.run_sync(base_model.metadata.create_all)


_db_service_instance: DBService | None = None

def get_db_service(config_service: ConfigService = Depends(get_config_service)) -> DBService:
    global _db_service_instance
    if _db_service_instance is None:
        _db_service_instance = DBService(config_service)
    return _db_service_instance