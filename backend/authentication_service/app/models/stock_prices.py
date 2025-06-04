from sqlalchemy import Column, Date, Float, Integer, ForeignKey, BigInteger, String
from .base import Base, BaseModel

class StockPrice(BaseModel, Base):
    date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    company_id = Column(ForeignKey("company.id"), nullable=True, index=True)
    ticker = Column(String, nullable=True)
