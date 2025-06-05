from sqlalchemy import Column, Integer, String, ForeignKey
from .base import Base, BaseModel

class WatchlistItem(BaseModel, Base):
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    stock_symbol = Column(String, nullable=False)
