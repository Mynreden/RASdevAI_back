from fastapi import APIRouter, Depends, HTTPException, Path, status, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import User, WatchlistItem

class WatchlistController:
    def __init__(self):
        self.router = APIRouter(prefix="/watchlist", tags=["watchlist"])
        self.register_routes()

    def register_routes(self):
        @self.router.get("/", response_model=dict)
        async def get_watchlist(db: AsyncSession = Depends(get_db), request: Request = None):
            email = request.state.user_email
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            result = await db.execute(select(WatchlistItem).filter(WatchlistItem.user_id == user.id))
            items = result.scalars().all()
            return {"watchlist": [item.stock_symbol for item in items]}

        @self.router.post("/add")
        async def add_to_watchlist(
            stock_symbol: str = Body(..., embed=True),
            db: AsyncSession = Depends(get_db),
            request: Request = None
        ):
            email = request.state.user_email
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            result = await db.execute(
                select(WatchlistItem).filter(WatchlistItem.user_id == user.id, WatchlistItem.stock_symbol == stock_symbol)
            )
            existing = result.scalars().first()
            if existing:
                raise HTTPException(status_code=400, detail="Stock already in watchlist")
            new_item = WatchlistItem(user_id=user.id, stock_symbol=stock_symbol)
            db.add(new_item)
            await db.commit()
            return {"message": "Stock added to watchlist"}

        @self.router.delete("/{ticker}")
        async def remove_from_watchlist(
            ticker: str = Path(..., description="Stock ticker to remove from watchlist"),
            db: AsyncSession = Depends(get_db),
            request: Request = None
        ):
            email = request.state.user_email
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            result = await db.execute(
                select(WatchlistItem).filter(WatchlistItem.user_id == user.id, WatchlistItem.stock_symbol == ticker)
            )
            item = result.scalars().first()
            if not item:
                raise HTTPException(status_code=404, detail="Stock not in watchlist")
            await db.delete(item)
            await db.commit()
            return {"message": "Stock removed from watchlist"}

    def get_router(self):
        return self.router