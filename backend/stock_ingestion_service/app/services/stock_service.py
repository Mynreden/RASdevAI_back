from datetime import datetime, timedelta
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from sqlalchemy.sql import func

from ..schemas import StockResponse, MiniChartData
from ..database import get_db
from ..models import Company, StockPrice


class StockService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_top_tickers(self, days: int = 7, active_within_days: int = 14) -> list[int]:
        
        today = datetime.utcnow().date()
        cutoff_date = today - timedelta(days=active_within_days)

        # Подзапрос с row_number
        subquery = (
            select(
                StockPrice.company_id,
                StockPrice.id,
                StockPrice.date,
                StockPrice.volume,
                func.row_number().over(
                    partition_by=StockPrice.company_id,
                    order_by=StockPrice.date.desc()
                ).label('row_num'),
            )
            .subquery()
        )

        # Фильтрация только по активным компаниям (у которых есть данные за последние N дней)
        stmt = (
            select(subquery.c.company_id)
            .where(
                subquery.c.row_num <= days,
                subquery.c.date >= cutoff_date  # фильтруем по дате последней активности
            )
            .group_by(subquery.c.company_id)
            .having(func.count() >= 3)  # например, минимум 3 записи
            .order_by(func.sum(subquery.c.volume).desc())
            .limit(5)
        )

        result = await self.db.execute(stmt)
        top_ids = [row[0] for row in result.all()]
        print("Top active tickers:", top_ids)
        return top_ids

    async def fetch_price_data(self, company_ids: list[int], days: int = 14) -> list[StockPrice]:
        today = datetime.now().date()
        week_ago = today - timedelta(days=days)

        stmt = (
            select(StockPrice)
            .where(StockPrice.company_id.in_(company_ids), StockPrice.date >= week_ago)
            .order_by(StockPrice.date.asc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    
    async def fetch_company_info(self, company_ids: list[int]) -> list[Company]:
        stmt = select(Company).where(Company.id.in_(company_ids))
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def process_stock_data(self, price_data: list[StockPrice], company_data: list[Company], company_ids: list[int]) -> list[StockResponse]:
        # Create company lookup dictionary
        company_dict = {c.id: c for c in company_data}
        
        price_dict = {}
        for price in price_data:
            if price.company_id not in price_dict:
                price_dict[price.company_id] = []
            price_dict[price.company_id].append(price)

        result = []
        for company_id in company_ids:
            if company_id not in company_dict or company_id not in price_dict:
                continue

            company = company_dict[company_id]
            ticker_prices = sorted(price_dict[company_id], key=lambda x: x.date)

            if not ticker_prices:
                continue

            mini_chart_data = [
                MiniChartData(date=str(price.date), value=round(price.close, 2))
                for price in ticker_prices
            ]
            current_price = ticker_prices[-1].close
            first_price = ticker_prices[-2].close
            share_change = round((current_price - first_price) / current_price * 100, 2)

            result.append(StockResponse(
                logoUrl=company.image_url or "https://via.placeholder.com/32",
                companyName=company.shortname or company.ticker,
                ticker=company.ticker,
                shareChange=share_change,
                currentPrice=round(current_price, 2),
                priceData=mini_chart_data
            ))
        return result

    async def get_popular_stocks(self) -> list[StockResponse]:
        top_company_ids = await self.fetch_top_tickers()
        if not top_company_ids:
            return []
        price_data = await self.fetch_price_data(top_company_ids, days=30)
        company_data = await self.fetch_company_info(top_company_ids)
        return await self.process_stock_data(price_data, company_data, top_company_ids)

    async def fetch_top_moves(self, days: int = 20) -> list[int]:
        today = datetime.now().date()
        week_ago = today - timedelta(days=days)

        # Get price changes
        stmt = (
            select(StockPrice.company_id, StockPrice.close)
            .where(StockPrice.date >= week_ago)
            .order_by(StockPrice.company_id, StockPrice.date)
        )
        print("dsfsdf")
        result = await self.db.execute(stmt)
        prices = result.all()
        print("dsfsdf")

        # Calculate price changes
        company_changes = {}
        current_company = None
        prev_price = None

        for price in prices:
            company_id, close  = price
            if company_id != current_company:
                current_company = company_id
                prev_price = None
            if prev_price is not None:
                price_change = (close - prev_price)/close
                company_changes[company_id] = price_change
            prev_price = close
        print("dsfsdf")

        # Sort by price change
        sorted_changes = sorted(
            company_changes.items(),
            key=lambda x: x[1] if x[1] is not None else float('-inf'),
            reverse=True
        )
        print("dsfsdf")

        return [company_id[0] for company_id in sorted_changes[:5]]

    async def get_top_moves(self) -> list[StockResponse]:
        company_ids = await self.fetch_top_moves()
        if not company_ids:
            return []
        print(company_ids)
        price_data = await self.fetch_price_data(company_ids, days=30)
        company_data = await self.fetch_company_info(company_ids)
        return await self.process_stock_data(price_data, company_data, company_ids)
    
    async def fetch_company_info_by_ticker(self, ticker: str) -> list[Company]:
        stmt = select(Company).where(Company.ticker == ticker.upper())
        result = await self.db.execute(stmt)
        return result.scalars().all()


def get_stock_service(db: AsyncSession = Depends(get_db)) -> StockService:
    return StockService(db)