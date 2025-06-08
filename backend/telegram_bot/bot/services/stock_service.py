import httpx
from bot.config import settings
from ..schemas import CompanySchema, NewsItem, StockResponse, LSTMForecastResponse
from pydantic import BaseModel, TypeAdapter

CompaniesAdapter = TypeAdapter(list[CompanySchema])
NewsAdapter = TypeAdapter(list[NewsItem])
NewsAdapter = TypeAdapter(list[NewsItem])


class StockService:
    def __init__(self):
        self.stock_service_url = settings.SERVICE_URL

    async def get_companies(self) -> list[CompanySchema]:
        url = f"{self.stock_service_url}/api/companies/"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers={"accept": "application/json"})
                response.raise_for_status() 
                companies = CompaniesAdapter.validate_json(response.text)
                return companies
            except httpx.RequestError as e:
                print(f"Request failed: {repr(e)}")
                return []

    async def get_news(self, ticker: str) -> list[NewsItem]:
        url = f"{self.stock_service_url}/api/news/{ticker}?limit=10&offset=0"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers={"accept": "application/json"})
                response.raise_for_status() 
                news = NewsAdapter.validate_json(response.text)
                return news
            except httpx.RequestError as e:
                print(f"Request failed: {repr(e)}")
                return []
            
    async def get_forecast(self, ticker, days=10) -> LSTMForecastResponse:
        url = f"{self.stock_service_url}/api/forecast/{ticker}?forecast_days={days}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers={"accept": "application/json"})
                response.raise_for_status() 
                forecast = LSTMForecastResponse.model_validate_json(response.text)
                return forecast
            except httpx.RequestError as e:
                print(f"Request failed: {repr(e)}")
                return []
            
    async def get_price_history(self, ticker, days=10) -> StockResponse:
        url = f"{self.stock_service_url}/api/stocks/by-ticker/{ticker}?days={days}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers={"accept": "application/json"})
                response.raise_for_status() 
                stock_response = StockResponse.model_validate_json(response.text)
                return stock_response
            except httpx.RequestError as e:
                print(f"Request failed: {repr(e)}")
                return []
