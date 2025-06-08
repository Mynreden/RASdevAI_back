from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import User, SubscriptionType
from datetime import datetime, timedelta

class SubscriptionController:
    def __init__(self):
        self.router = APIRouter(prefix="/subscription", tags=["subscription"])
        self.register_routes()

    def register_routes(self):
        @self.router.get("/", response_model=dict)
        async def get_subscription_status(
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

            return {
                "subscription_type": user.subscription_type.value,
                "expire_date": user.subscription_expire_date
            }

        @self.router.put("/update", response_model=dict)
        async def update_subscription(
            subscription_type: SubscriptionType = Body(..., embed=True),
            duration_days: int = Body(30, embed=True),
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

            user.subscription_type = subscription_type
            user.subscription_expire_date = datetime.utcnow() + timedelta(days=duration_days)

            await db.commit()

            return {
                "message": "Subscription updated successfully",
                "subscription_type": user.subscription_type.value,
                "expire_date": user.subscription_expire_date
            }

    def get_router(self):
        return self.router
