# schemas.py
from pydantic import BaseModel

class PortfolioItemCreate(BaseModel):
    ticker: str
    shares: int
    price: float

class PortfolioItemResponse(BaseModel):
    ticker: str
    shares: int
    price: float
