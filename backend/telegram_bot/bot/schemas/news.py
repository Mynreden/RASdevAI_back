from pydantic import BaseModel, model_validator
from datetime import datetime
from typing import Optional


class SentimentsProbs(BaseModel):
    neutral: float
    positive: float
    negative: float


class NewsFromRabbit(BaseModel):
    ticker: str
    id: int
    create_datetime: str
    language: str
    subject: str
    body: str
    is_important: bool
    sentiment_probs: SentimentsProbs

    class Config:
        extra = "ignore"


class NewsItem(BaseModel):
    title: str
    content: Optional[str] = ""
    source: str
    date: datetime
    neutral: float
    positive: float
    negative: float
    
    class Config:
        from_attributes=True
