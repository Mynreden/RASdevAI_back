from sqlalchemy import Column, Integer, String, ForeignKey, Float, CheckConstraint
from .base import Base, BaseModel

class AlertItem(BaseModel, Base):
    __tablename__ = 'alert_item'

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    stock_symbol = Column(String, nullable=False)
    less_than = Column(Float, nullable=True)
    more_than = Column(Float, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "(less_than IS NULL AND more_than IS NOT NULL) OR (less_than IS NOT NULL AND more_than IS NULL)",
            name="only_one_threshold_check"
        ),
    )

    def __repr__(self):
        direction = "above" if self.more_than is not None else "below"
        threshold = self.more_than if self.more_than is not None else self.less_than
        return f"<AlertItem user_id={self.user_id} stock_symbol='{self.stock_symbol}' alert_if_{direction}={threshold}>"