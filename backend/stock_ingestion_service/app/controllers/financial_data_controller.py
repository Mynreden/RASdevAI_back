from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.database import get_db

from ..models import FinancialData
from ..schemas import FinancialDataItem
import traceback

class FinancialDataController:
    def __init__(self):
        self.router = APIRouter(prefix="/financial", tags=["financial"])
        self.register_routes()

    def __init__(self):
        self.router = APIRouter(prefix="/financial", tags=["financial"])
        self.register_routes()

    def register_routes(self):
        @self.router.get("/latest/{ticker}", response_model=FinancialDataItem)
        async def get_latest_financial(
            ticker: str,
            db: AsyncSession = Depends(get_db)
        ):
            try:
                stmt = (
                    select(FinancialData)
                    .where(FinancialData.ticker == ticker)
                    .order_by(FinancialData.change_date.desc())
                    .limit(1)
                )
                result = await db.execute(stmt)
                latest = result.scalar_one_or_none()
                if not latest:
                    raise HTTPException(status_code=404, detail=f"No financial data found for {ticker}")
                return latest
            except Exception as e:
                error_trace = traceback.format_exc()
                raise HTTPException(status_code=500, detail=f"{str(e)}\n{error_trace}")

        @self.router.get("/{ticker}", response_model=list[FinancialDataItem])
        async def get_last_quarters(
            ticker: str,
            quartals: int = Query(4, ge=1, le=20),
            db: AsyncSession = Depends(get_db)
        ):
            try:
                stmt = (
                    select(FinancialData)
                    .where(FinancialData.ticker == ticker)
                    .order_by(FinancialData.change_date.desc())
                    .limit(quartals)
                )
                result = await db.execute(stmt)
                records = result.scalars().all()
                if not records:
                    raise HTTPException(status_code=404, detail=f"No financial data found for {ticker}")
                return records
            except Exception as e:
                error_trace = traceback.format_exc()
                raise HTTPException(status_code=500, detail=f"{str(e)}\n{error_trace}")

    def get_router(self):
        return self.router


    def get_router(self):
        return self.router
