# portfolio_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from ..models import User, PortfolioItem
from ..schemas import PortfolioItemCreate, PortfolioItemResponse

class PortfolioController:
    def __init__(self):
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

    async def _get_user_by_email(self, email: str, db: AsyncSession) -> User:
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    
    
    def get_router(self):
        return self.router
