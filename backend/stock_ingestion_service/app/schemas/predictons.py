from pydantic import BaseModel
from typing import List

class LSTMDayRequest(BaseModel):
    ticker: str
    days: List[List[float]]
    forecast_days: int

class LSTMForecastResponse(BaseModel):
    forecast_days: int
    predicted_prices: List[float]

class LSTMForecastResponseMonth(BaseModel):
    predicted_prices: List[float]