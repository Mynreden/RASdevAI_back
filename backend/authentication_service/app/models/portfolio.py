# models.py
from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, BaseModel

class PortfolioItem(BaseModel, Base):
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    ticker = Column(String, nullable=False)
    shares = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    user = relationship("User", back_populates="portfolio")

