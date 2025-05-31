from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy.sql import func

Base = declarative_base()

class BaseModel:
    id = Column(Integer, primary_key=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
