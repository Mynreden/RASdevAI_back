from sqlalchemy import Column, String
from .base import Base, BaseModel

class Company(BaseModel, Base):
    ticker = Column(String, unique=True, index=True, nullable=False)
    shortname = Column(String, nullable=False)
    longname = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    address = Column(String, nullable=True)
    website = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    summary = Column(String, nullable=True)
