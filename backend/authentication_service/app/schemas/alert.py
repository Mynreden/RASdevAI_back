from pydantic import BaseModel, field_validator, model_validator
from typing import Optional

class AlertCreate(BaseModel):
    stock_symbol: str
    less_than: Optional[float] = None
    more_than: Optional[float] = None

    @model_validator(mode="after")
    def check_only_one_threshold(self):
        if (self.less_than is None and self.more_than is None) or \
           (self.less_than is not None and self.more_than is not None):
            raise ValueError("Exactly one of 'less_than' or 'more_than' must be set.")
        return self


class AlertResponse(BaseModel):
    id: int
    user_id: int
    stock_symbol: str
    less_than: Optional[float]
    more_than: Optional[float]

    class Config:
        orm_mode = True
