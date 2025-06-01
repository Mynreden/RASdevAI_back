from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
import datetime
from .base import Base, BaseModel

class EmailLog(BaseModel, Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    cc = Column(ARRAY(String), nullable=True)
    bcc = Column(ARRAY(String), nullable=True)
    attachments = Column(ARRAY(String), nullable=True)
    status = Column(String, default="sent")  # sent | failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
