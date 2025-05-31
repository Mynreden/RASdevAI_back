from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime
from .base import Base, BaseModel

class News(BaseModel, Base):
    ticker = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False, default="")
    neutral = Column(Float)
    positive = Column(Float)
    negative = Column(Float)
    source = Column(String, nullable=False, default="")
    important = Column(Boolean, nullable=True)
