from pydantic import BaseModel
from typing import Optional
from datetime import date

class FinancialDataFromRabbit(BaseModel):
    change_date: date
    units: Optional[str]
    currency: str
    net_profit: Optional[float]
    gross_income: Optional[float]
    own_capital: Optional[float]
    volume_sale: Optional[float]
    balance_assets_value: Optional[float]
    aggregate_assets: Optional[float]
    note: Optional[str]
    audited: Optional[bool]
    authorized_capital: Optional[float]
    net_assets_value: Optional[float]
    common_book_value: Optional[float]
    pref_book_value: Optional[float]
    conv_pref_book_value: Optional[float]
    total_liabilities: Optional[float]
    roe: Optional[float]
    roa: Optional[float]
    ros: Optional[float]
    ticker: str

class FinancialDataItem(BaseModel):
    ticker: str
    change_date: date
    units: Optional[str]
    currency: Optional[str]
    net_profit: Optional[float]
    own_capital: Optional[float]
    aggregate_assets: Optional[float]
    authorized_capital: Optional[float]
    common_book_value: Optional[float]
    total_liabilities: Optional[float]
    roe: Optional[float]
    roa: Optional[float]

    class Config:
        orm_mode = True
