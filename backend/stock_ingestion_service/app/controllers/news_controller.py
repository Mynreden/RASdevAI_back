from fastapi import APIRouter, Depends, HTTPException, Query
from ..services import NewsService, get_news_service
from ..schemas.news import NewsItem
from ..models import News
import traceback


class NewsController:
    def __init__(self):
        self.router = APIRouter(prefix="/news", tags=["news"])
        self.register_routes()

    def register_routes(self):
        @self.router.get("/", response_model=list[NewsItem])
        async def get_all_news(
            limit: int = Query(10, ge=1, le=100),
            offset: int = Query(0, ge=0),
            news_service: NewsService = Depends(get_news_service)
        ):
            try:
                return await news_service.get_news(limit=limit, offset=offset)
            except Exception as e:
                error_trace = traceback.format_exc()
                raise HTTPException(status_code=500, detail=f"{str(e)}\n{error_trace}")
            
        @self.router.get("/{ticker}", response_model=list[NewsItem])
        async def get_ticker_news(
            ticker: str,
            limit: int = Query(10, ge=1, le=100),
            offset: int = Query(0, ge=0),
            news_service: NewsService = Depends(get_news_service)
        ):
            try:
                return await news_service.get_news_by_ticker(ticker, limit=limit, offset=offset)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error fetching news for {ticker}: {str(e)}")
        
    def get_router(self):
        return self.router
