from sqlalchemy import Column, Integer, Float, String, Date, Boolean
from .base import Base, BaseModel

class FinancialData(BaseModel, Base):
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    change_date = Column(Date)
    units = Column(String)
    currency = Column(String)
    net_profit = Column(Float)
    own_capital = Column(Float)
    aggregate_assets = Column(Float)
    authorized_capital = Column(Float)
    common_book_value = Column(Float)
    total_liabilities = Column(Float)
    roe = Column(Float)
    roa = Column(Float)
