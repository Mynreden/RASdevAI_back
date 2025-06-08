from pydantic import BaseModel
from typing import Optional, List
from .financial_data import FinancialDataItem
from .news import NewsItem
from .stock_data import StockResponse
class LLMPromptRequest(BaseModel):
    message: str


class RecentCompanyDataResponse(BaseModel):
    financial_data: List[FinancialDataItem]
    news: List[NewsItem]
    stock: Optional[StockResponse]
