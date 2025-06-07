from pydantic import BaseModel
from datetime import date

class MiniChartData(BaseModel):
    date: str
    value: float

class StockResponse(BaseModel):
    logoUrl: str
    companyName: str
    ticker: str
    shareChange: float
    currentPrice: float
    priceData: list[MiniChartData]
