import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Integer, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
import datetime

# === SQLAlchemy модель ===
Base = declarative_base()

class Company(Base):
    __tablename__ = "company"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True, nullable=False)
    shortname = Column(String, nullable=False)
    longname = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    address = Column(String, nullable=True)
    website = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    summary = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)


# === Подключение к Supabase PostgreSQL ===
DATABASE_URL = "postgresql://postgres.ghskobldjvaxulgbddds:Qwertys1234Qwertys!@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()
# === Создание таблицы ===
Base.metadata.create_all(bind=engine)
print("✅ Таблица 'company' успешно создана")

# === Чтение CSV ===
df = pd.read_csv("company.csv", header=None)

# Назначаем колонки вручную (в том же порядке, что и в твоем примере)
df.columns = [
    "ticker", "shortname", "longname", "industry", "sector", "country",
    "city", "address", "website", "image_url", "summary", "id",
    "created_at", "updated_at", "is_deleted"
]

# Преобразование типов
df["created_at"] = pd.to_datetime(df["created_at"])
df["updated_at"] = pd.to_datetime(df["updated_at"])
df["is_deleted"] = df["is_deleted"].apply(lambda x: x == "t")

# === Запись в БД ===
companies = []
for _, row in df.iterrows():
    company = Company(
        id=row["id"],
        ticker=row["ticker"],
        shortname=row["shortname"],
        longname=row["longname"],
        industry=row["industry"],
        sector=row["sector"],
        country=row["country"],
        city=row["city"],
        address=row["address"],
        website=row["website"],
        image_url=row["image_url"],
        summary=row["summary"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        is_deleted=row["is_deleted"]
    )
    companies.append(company)

session.add_all(companies)
session.commit()
print(f"{len(companies)} companies inserted into the database.")
