import httpx
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from collections import defaultdict
from statistics import mean
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import LSTMForecastResponse, LSTMDayRequest
from ..database import get_db
from ..models import StockPrice, News
from .stock_service import StockService
from .news_service import NewsService
import os

class ForecastService:
    def __init__(self, db):
        self.ML_SERVICE_URL = "https://5d10-46-34-194-42.ngrok-free.app/lstm-day"
        self.db = db
        self.stock_service = StockService(db)
        self.news_service = NewsService(db)

    async def forecast_price(self, ticker: str, forecast_days: int) -> LSTMForecastResponse:
        try:
            company_id = await self._get_company_id(ticker)
            price_records = await self.stock_service.fetch_price_data([company_id], 60)

            if not price_records or len(price_records) < 60:
                raise HTTPException(status_code=400, detail="Not enough price data")

            news_records = await self.news_service.get_news_by_ticker(ticker, limit=200)

            sentiments_by_date = defaultdict(lambda: {"positive": [], "negative": [], "neutral": []})

            for news in news_records:
                date_str = news.date.date()
                sentiments_by_date[date_str]["positive"].append(news.positive)
                sentiments_by_date[date_str]["negative"].append(news.negative)
                sentiments_by_date[date_str]["neutral"].append(news.neutral)

            merged_days = []
            for record in price_records:
                date = record.date
                close_price = record.close

                sentiments = sentiments_by_date.get(date, {"positive": [0.0], "negative": [0.0], "neutral": [0.0]})
                merged_days.append([
                    close_price,
                    mean(sentiments["negative"]),
                    mean(sentiments["positive"]),
                    mean(sentiments["neutral"])
                ])

            if len(merged_days) < 60:
                raise HTTPException(status_code=400, detail="Insufficient merged data for 60 days")

            payload = LSTMDayRequest(ticker=ticker, days=merged_days, forecast_days=forecast_days).dict()
            async with httpx.AsyncClient() as client:
                response = await client.post(self.ML_SERVICE_URL, json=payload)

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"LSTM model error: {response.text}")

            result = response.json()
            return LSTMForecastResponse(
                forecast_days=result["forecast_days"],
                predicted_prices=result["predicted_prices"]
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def _get_company_id(self, ticker: str) -> int:
        stmt = select(StockPrice.company_id).where(StockPrice.ticker == ticker).limit(1)
        result = await self.db.execute(stmt)
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Company with ticker '{ticker}' not found")
        return row[0]
    
def get_forecast_service(db: AsyncSession = Depends(get_db)) -> ForecastService:
    return ForecastService(db)
