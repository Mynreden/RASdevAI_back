from fastapi import Depends
import httpx
from typing import List, Dict
from app.core import get_config_service, ConfigService
from app.schemas import StockResponse

class StockService:
    def __init__(self, config_service: ConfigService):
        self.base_url = config_service.get("STOCK_SERVICE_URL", None)
        if self.base_url is None:
            raise ValueError("VERIFICATION_SECRET_KEY is required")

    def get_history(self, ticker: str, days: int) -> StockResponse:
        url = f"{self.base_url}/by-ticker/{ticker}?days={days}"

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
                parsed = StockResponse.model_validate(data)
                return parsed
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ошибка при получении данных по {ticker}: {e}")

def get_stock_service(config_service: ConfigService = Depends(get_config_service)) -> StockService:
    """Функция зависимости для предоставления экземпляра StockService."""
    return StockService(config_service=config_service)
