# portfolio_controller.py
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Path
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from ..services import RabbitService, get_rabbit_service
from ..core import ConfigService, get_config_service
from ..models import User, PortfolioItem
from ..schemas import PortfolioItemCreate, PortfolioItemResponse

class PortfolioController:
    def __init__(self, config_service: ConfigService):
        self.router = APIRouter(prefix="/portfolio", tags=["portfolio"])
        self.register_routes()

    def register_routes(self):
        @self.router.get("/", response_model=list[PortfolioItemResponse])
        async def get_portfolio(
            db: AsyncSession = Depends(get_db),
            request: Request = None
        ):
            email = request.headers.get("X-User-Email")
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

            user = await self._get_user_by_email(email, db)
            result = await db.execute(select(PortfolioItem).filter(PortfolioItem.user_id == user.id))
            items = result.scalars().all()

            return [
                PortfolioItemResponse(ticker=item.ticker, shares=item.shares, price=item.price)
                for item in items
            ]

        @self.router.post("/", status_code=201)
        async def add_to_portfolio(
            item: PortfolioItemCreate,
            db: AsyncSession = Depends(get_db),
            request: Request = None
        ):
            email = request.headers.get("X-User-Email")
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

            user = await self._get_user_by_email(email, db)

            new_item = PortfolioItem(
                user_id=user.id,
                ticker=item.ticker,
                shares=item.shares,
                price=item.price
            )
            db.add(new_item)
            await db.commit()
            return {"message": "Stock added to portfolio"}

        @self.router.delete("/{ticker}")
        async def delete_from_portfolio(
            ticker: str = Path(...),
            db: AsyncSession = Depends(get_db),
            request: Request = None
        ):
            email = request.headers.get("X-User-Email")
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

            user = await self._get_user_by_email(email, db)
            result = await db.execute(select(PortfolioItem).filter(
                PortfolioItem.user_id == user.id, PortfolioItem.ticker == ticker
            ))
            item = result.scalars().first()
            if not item:
                raise HTTPException(status_code=404, detail="Stock not found in portfolio")

            await db.delete(item)
            await db.commit()
            return {"message": f"{ticker} removed from portfolio"}
        
        from collections import defaultdict

        @self.router.get("/history", response_model=dict)
        async def get_portfolio_value_history(
            days: int = Query(30, ge=1),
            db: AsyncSession = Depends(get_db),
            request: Request = None,
            rabbit_service: RabbitService = Depends(get_rabbit_service)
        ):
            email = request.headers.get("X-User-Email")
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

            user = await self._get_user_by_email(email, db)
            result = await db.execute(select(PortfolioItem).filter(PortfolioItem.user_id == user.id))
            items = result.scalars().all()
            if not items:
                return {}

            ticker_to_shares = {item.ticker: item.shares for item in items}
            daily_values = defaultdict(float)

            for ticker, shares in ticker_to_shares.items():
                try:
                    await rabbit_service.send_message({
                        "ticker": ticker,
                        "days": days
                    })

                    response_data = await rabbit_service.receive_message(timeout=30)

                    for entry in response_data:
                        daily_values[entry["date"]] += shares * entry["close"]
                except Exception as e:
                    print(f"❌ Ошибка при получении данных по {ticker}: {e}")
                    raise HTTPException(status_code=502, detail=f"Ошибка при получении данных по {ticker}: {e}")

            return dict(daily_values)

    
    async def _get_user_by_email(self, email: str, db: AsyncSession) -> User:
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    
    
    def get_router(self):
        return self.router
