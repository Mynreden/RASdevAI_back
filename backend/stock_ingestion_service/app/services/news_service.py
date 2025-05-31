from datetime import datetime
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from ..schemas.news import NewsItem
from ..core import logger
from ..models import News
from ..database import get_db


class NewsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_news(self, limit: int = 10, offset: int = 0) -> list[NewsItem]:
        stmt = select(News).order_by(desc(News.date)).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        news_list = result.scalars().all()
        return [NewsItem.from_orm(news) for news in news_list]

    async def get_news_by_ticker(self, ticker: str, limit: int = 10, offset: int = 0):
        stmt = select(News).filter(News.ticker == ticker).order_by(desc(News.date)).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        news_list = result.scalars().all()
        return [NewsItem.from_orm(news) for news in news_list]

def get_news_service(db: AsyncSession = Depends(get_db)) -> NewsService:
    return NewsService(db)
