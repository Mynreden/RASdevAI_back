import httpx
from datetime import datetime, timedelta, date
from fastapi import HTTPException, Depends
from collections import defaultdict
from statistics import mean
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import LSTMForecastResponse, LSTMDayRequest, LSTMForecastResponseMonth
from ..database import get_db
from ..models import StockPrice, News
from .stock_service import StockService
from .news_service import NewsService
from ..redis import get_redis_client, PricePredictionRedis  
import os

class ForecastService:
    def __init__(self, db, redis: PricePredictionRedis):
        self.ML_SERVICE_URL = "http://164.90.167.226:8100/lstm-day"
        self.ML_SERVICE_MONTH_URL = "http://164.90.167.226:8100/lstm-month"
        self.db = db
        self.redis = redis
        self.stock_service = StockService(db)
        self.news_service = NewsService(db)
        self.day_lstm_history_limit = 60
        self.month_lstm_history_limit_in_days = 200
        self.month_lstm_history_limit_in_month = 6


    async def forecast_price(self, ticker: str, forecast_days: int) -> LSTMForecastResponse:
        try:
            today = date.today()
            cached = await self.redis.get_predictions(today, ticker, prefix="day")
            
            if cached:
                print("Using cached data")
                return LSTMForecastResponse(
                    forecast_days=forecast_days,
                    predicted_prices=cached
                )
            print("Fetching fresh data")
            company_id = await self._get_company_id(ticker)
            price_records = await self.stock_service.fetch_price_data([company_id], self.day_lstm_history_limit * 2)

            if not price_records or len(price_records) < self.day_lstm_history_limit:
                raise HTTPException(status_code=400, detail="Not enough price data")

            price_records = price_records[-self.day_lstm_history_limit:]
            news_records = await self.news_service.get_news_by_ticker(ticker, limit=200)

            sentiments_by_date = defaultdict(lambda: {"positive": [], "negative": [], "neutral": []})

            for news in news_records:
                date_str = news.date.date()
                sentiments_by_date[date_str]["positive"].append(news.positive)
                sentiments_by_date[date_str]["negative"].append(news.negative)
                sentiments_by_date[date_str]["neutral"].append(news.neutral)

            merged_days = []
            for record in price_records:
                record_date = record.date
                close_price = record.close
                sentiments = sentiments_by_date.get(record_date, {"positive": [0.0], "negative": [0.0], "neutral": [0.0]})
                merged_days.append([
                    close_price,
                    mean(sentiments["negative"]),
                    mean(sentiments["positive"]),
                    mean(sentiments["neutral"])
                ])

            if len(merged_days) < self.day_lstm_history_limit:
                raise HTTPException(status_code=400, detail="Insufficient merged data")

            payload = LSTMDayRequest(ticker=ticker, days=merged_days, forecast_days=forecast_days).dict()
            async with httpx.AsyncClient() as client:
                response = await client.post(self.ML_SERVICE_URL, json=payload)

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"LSTM model error: {response.text}")

            result = response.json()
            predicted_prices = result["predicted_prices"]

            await self.redis.save_predictions(today, ticker, predicted_prices, prefix="day")

            return LSTMForecastResponse(
                forecast_days=forecast_days,
                predicted_prices=predicted_prices
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def forecast_price_monthly(self, ticker: str, forecast_months: int) -> LSTMForecastResponseMonth:
        try:
            today = date.today()
            cached = await self.redis.get_predictions(today, ticker, prefix="month")
            if cached:
                return LSTMForecastResponseMonth(predicted_prices=cached)

            company_id = await self._get_company_id(ticker)
            price_records = await self.stock_service.fetch_price_data([company_id], self.month_lstm_history_limit_in_days * 2)

            if not price_records or len(price_records) < self.month_lstm_history_limit_in_days:
                raise HTTPException(status_code=400, detail="Not enough price data for 6 months")

            news_records = await self.news_service.get_news_by_ticker(ticker, limit=1000)
            sentiments_by_date = defaultdict(lambda: {"positive": [], "negative": [], "neutral": []})

            for news in news_records:
                date_str = news.date.date()
                sentiments_by_date[date_str]["positive"].append(news.positive)
                sentiments_by_date[date_str]["negative"].append(news.negative)
                sentiments_by_date[date_str]["neutral"].append(news.neutral)

            monthly_data = defaultdict(lambda: {
                "prices": [],
                "volumes": [],
                "sentiments": {"positive": [], "negative": [], "neutral": []}
            })

            for record in price_records:
                record_date = record.date
                month_key = (record_date.year, record_date.month)

                open_price = getattr(record, 'open', record.close)
                high_price = getattr(record, 'high', record.close)
                low_price = getattr(record, 'low', record.close)
                close_price = record.close

                avg_price = mean([open_price, high_price, low_price, close_price])
                monthly_data[month_key]["prices"].append(avg_price)

                volume_data = getattr(record, 'volume', 0)
                avg_volume = mean(volume_data) if isinstance(volume_data, list) else volume_data
                monthly_data[month_key]["volumes"].append(avg_volume)

                sentiments = sentiments_by_date.get(record_date, {
                    "positive": [0.0], 
                    "negative": [0.0], 
                    "neutral": [1.0]
                })

                monthly_data[month_key]["sentiments"]["positive"].extend(sentiments["positive"])
                monthly_data[month_key]["sentiments"]["negative"].extend(sentiments["negative"])
                monthly_data[month_key]["sentiments"]["neutral"].extend(sentiments["neutral"])

            sorted_months = sorted(monthly_data.keys())[-self.month_lstm_history_limit_in_month:]

            if len(sorted_months) < self.month_lstm_history_limit_in_month:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient monthly data: {len(sorted_months)} months, need {self.month_lstm_history_limit_in_month}"
                )

            sequence = []
            for month_key in sorted_months:
                month_info = monthly_data[month_key]

                avg_price = mean(month_info["prices"]) if month_info["prices"] else 0
                avg_volume = mean(month_info["volumes"]) if month_info["volumes"] else 0
                avg_neutral = mean(month_info["sentiments"]["neutral"]) if month_info["sentiments"]["neutral"] else 1.0
                avg_positive = mean(month_info["sentiments"]["positive"]) if month_info["sentiments"]["positive"] else 0.0
                avg_negative = mean(month_info["sentiments"]["negative"]) if month_info["sentiments"]["negative"] else 0.0

                sequence.append([
                    float(avg_neutral),
                    float(avg_positive),
                    float(avg_negative),
                    float(avg_price),
                    float(avg_volume)
                ])

            if len(sequence) != self.month_lstm_history_limit_in_month:
                raise HTTPException(
                    status_code=400,
                    detail=f"Expected {self.month_lstm_history_limit_in_month} monthly data points, got {len(sequence)}"
                )

            payload = {
                "ticker": ticker,
                "sequence": sequence,
                "forecast_months": forecast_months
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.ML_SERVICE_MONTH_URL, json=payload)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=500, 
                    detail=f"LSTM monthly model error: {response.text}"
                )

            result = response.json()
            predicted_prices = result["predicted_prices"]

            # ✅ Cache the result
            await self.redis.save_predictions(today, ticker, predicted_prices, prefix="month")

            return LSTMForecastResponseMonth(predicted_prices=predicted_prices)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Monthly forecast error: {str(e)}")
            
    async def _get_company_id(self, ticker: str) -> int:
        stmt = select(StockPrice.company_id).where(StockPrice.ticker == ticker).limit(1)
        result = await self.db.execute(stmt)
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Company with ticker '{ticker}' not found")
        return row[0]

async def get_forecast_service(
    db: AsyncSession = Depends(get_db),
    redis: PricePredictionRedis = Depends(get_redis_client)
) -> ForecastService:
    return ForecastService(db, redis)
