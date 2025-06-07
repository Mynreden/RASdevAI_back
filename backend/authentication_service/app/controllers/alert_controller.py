from fastapi import APIRouter, Depends, HTTPException, Request, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import User, AlertItem
from app.schemas.alert import AlertCreate, AlertResponse

class AlertController:
    def __init__(self):
        self.router = APIRouter(prefix="/alerts", tags=["alerts"])
        self.register_routes()

    def register_routes(self):
        @self.router.get("/", response_model=dict)
        async def get_alerts(db: AsyncSession = Depends(get_db), request: Request = None):
            email = request.state.user_email
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            result = await db.execute(select(AlertItem).filter(AlertItem.user_id == user.id))
            alerts = result.scalars().all()

            return {"alerts": [AlertResponse.from_orm(alert) for alert in alerts]}

        @self.router.post("/add", response_model=AlertResponse)
        async def add_alert(
            alert_data: AlertCreate = Body(...),
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

            new_alert = AlertItem(
                user_id=user.id,
                stock_symbol=alert_data.stock_symbol,
                less_than=alert_data.less_than,
                more_than=alert_data.more_than
            )

            db.add(new_alert)
            await db.commit()
            await db.refresh(new_alert)

            return AlertResponse.from_orm(new_alert)

        @self.router.delete("/{alert_id}")
        async def delete_alert(
            alert_id: int,
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

            result = await db.execute(select(AlertItem).filter(AlertItem.id == alert_id, AlertItem.user_id == user.id))
            alert = result.scalars().first()
            if not alert:
                raise HTTPException(status_code=404, detail="Alert not found")

            await db.delete(alert)
            await db.commit()
            return {"message": "Alert deleted"}

    def get_router(self):
        return self.router
