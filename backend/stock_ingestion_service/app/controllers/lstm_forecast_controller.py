from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core import config_service, get_config_service
from ..services import ForecastService, get_forecast_service
from ..schemas import LSTMForecastResponse, LSTMForecastResponseMonth
import traceback

class LSTMForecastController:
    def __init__(self):
        self.router = APIRouter(prefix="/forecast", tags=["forecast"])
        self.register_routes()

    def register_routes(self):
        config_service =  get_config_service()
        @self.router.get("/{ticker}", response_model=LSTMForecastResponse)
        async def forecast_price(
            ticker: str,
            forecast_days: int = Query(5, ge=1, le=90),
            service: ForecastService = Depends(get_forecast_service)
        ):
            try:
                result = await service.forecast_price(ticker)
                result = LSTMForecastResponse(predicted_prices=result.predicted_prices[:forecast_days])
                return result
            except Exception as e:
                error_trace = traceback.format_exc()
                raise HTTPException(status_code=500, detail=f"Error predicting for {ticker}:\n{str(e)}\n{error_trace}")
        
        @self.router.get("/monthly/{ticker}", response_model=LSTMForecastResponseMonth)
        async def forecast_price_monthly(
            ticker: str,
            forecast_month: int = Query(1, ge=1, le=30),
            service: ForecastService = Depends(get_forecast_service)
        ):
            try:
                result = await service.forecast_price_monthly(ticker)
                result = LSTMForecastResponseMonth(predicted_prices=result.predicted_prices[:forecast_month])
                return result
            except Exception as e:
                error_trace = traceback.format_exc()
                raise HTTPException(status_code=500, detail=f"Error predicting for {ticker}:\n{str(e)}\n{error_trace}")
        
        @self.router.get("/clear", response_model=int)
        async def clear_forecast(
            ticker: Optional[str] = Query(None),
            prefix: Optional[str] = Query(None),
            service: ForecastService = Depends(get_forecast_service)
        ):
            try:
                result = await service.clear_predictions(ticker=ticker, prefix=prefix)
                return result
            except Exception as e:
                error_trace = traceback.format_exc()
                raise HTTPException(status_code=500, detail=f"Error clearing forecast:\n{str(e)}\n{error_trace}")
    
    def get_router(self):
        return self.router
