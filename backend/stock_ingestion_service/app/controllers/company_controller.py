from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import Company
from app.schemas import CompanySchema

class CompanyController:
    def __init__(self):
        self.router = APIRouter(prefix="/companies", tags=["companies"])
        self.register_routes()

    def register_routes(self):
        @self.router.get("/", response_model=list[CompanySchema])
        async def get_all_companies(db: AsyncSession = Depends(get_db)):
            try:
                result = await db.execute(select(Company).where(Company.is_deleted == False))
                companies = result.scalars().all()
                return companies
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving companies: {str(e)}")

        @self.router.get("/{ticker}", response_model=CompanySchema)
        async def get_company_by_ticker(
            ticker: str,
            db: AsyncSession = Depends(get_db)):
            """Получить данные по конкретной компании по тикеру."""
            try:
                result = await db.execute(select(Company).where(Company.is_deleted == False, Company.ticker == ticker))
                companies = result.scalars().first()
                return companies
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving companies: {str(e)}")

    def get_router(self):
        return self.router
