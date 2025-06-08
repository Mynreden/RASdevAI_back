from pydantic import BaseModel
from typing import Optional

class CompanySchema(BaseModel):
    id: int
    ticker: str
    shortname: str
    longname: str
    industry: Optional[str]
    sector: Optional[str]
    country: Optional[str]
    city: Optional[str]
    address: Optional[str]
    website: Optional[str]
    image_url: Optional[str]
    summary: Optional[str]

    class Config:
        orm_mode = True
