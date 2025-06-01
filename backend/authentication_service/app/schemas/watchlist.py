from pydantic import BaseModel, Field

class WatchlistItemBase(BaseModel):
    stock_symbol: str = Field(min_length=1, max_length=10, description="Stock ticker symbol")

class WatchlistResponse(BaseModel):
    watchlist: list[str] = Field(description="List of stock symbols in user's watchlist")

