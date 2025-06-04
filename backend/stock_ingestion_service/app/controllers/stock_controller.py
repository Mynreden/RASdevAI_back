from fastapi import APIRouter, Depends, HTTPException, Query

from ..services import StockService, get_stock_service
from ..schemas import StockResponse
from ..core import logger

class StockController:
    def __init__(self):
        self.router = APIRouter(prefix="/stocks", tags=["stocks"])
        self.register_routes()

    def register_routes(self):
        @self.router.get("/popular", response_model=list[StockResponse])
        async def get_popular_stocks(
            stock_service: StockService = Depends(get_stock_service),
        ):
            try:
                return await stock_service.get_popular_stocks()
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/top-movers", response_model=list[StockResponse])
        async def get_top_movers(
            stock_service: StockService = Depends(get_stock_service),
        ):
            try:
                return await stock_service.get_top_moves()
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
            
        @self.router.get("/by-ticker/{ticker}", response_model=StockResponse)
        async def get_stock_by_ticker(
            ticker: str,
            days: int = Query(14, ge=1),
            stock_service: StockService = Depends(get_stock_service),
        ):
            """Получить данные по конкретной акции по тикеру."""
            try:
                # Получить компанию
                companies = await stock_service.fetch_company_info_by_ticker(ticker)
                if not companies:
                    raise HTTPException(status_code=404, detail="Компания не найдена")

                company = companies[0]
                company_id = company.id
                price_data = await stock_service.fetch_price_data([company_id], days)
                if not price_data:
                    raise HTTPException(status_code=404, detail="Нет ценовых данных")

                return (await stock_service.process_stock_data(price_data, [company], [company_id]))[0]
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

            
    def get_router(self):
        return self.router
