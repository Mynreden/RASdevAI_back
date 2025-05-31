from sqlalchemy import Column, String, Boolean, Enum, DateTime
from .base import Base, BaseModel
from sqlalchemy.orm import relationship
from .roles import UserRole
from .subscription import SubscriptionType

class User(BaseModel, Base):
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    auth_provider = Column(String, nullable=False, default="local")
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    social_id = Column(String, unique=True, index=True, nullable=True)
    profile_pic = Column(String, nullable=True)
    portfolio = relationship("PortfolioItem", back_populates="user", cascade="all, delete-orphan")
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    subscription_type = Column(Enum(SubscriptionType), default=SubscriptionType.FREE, nullable=False)
    subscription_expire_date = Column(DateTime, nullable=True)
