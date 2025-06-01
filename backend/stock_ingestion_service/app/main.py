import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn
from app.middlewares import register_middlewares
from app.controllers import StockController, NewsController, LLMController, CompanyController, FinancialDataController, LSTMForecastController
from dotenv import load_dotenv
from .database import DBService
from .core import ConfigService, get_config_service
from .models import Base
from app.services import RabbitService, get_rabbit_service
import os

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config_service = get_config_service()
    rabbit_service =get_rabbit_service(config_service=config_service)

    app.state.rabbit_service = rabbit_service

    consumer_task = asyncio.create_task(rabbit_service.start_consumers())
    print("✅ RabbitMQ consumer started")
    yield
    await rabbit_service.stop()
    consumer_task.cancel()
    print("🔌 RabbitMQ consumer stopped")

app = FastAPI(lifespan=lifespan, title="RASdevAI Stock Service")
# midlewares regustration
register_middlewares(app)

# controller registratiom
stock_controller = StockController()
app.include_router(stock_controller.get_router())
news_controller = NewsController()
app.include_router(news_controller.get_router())
llm_controller = LLMController()
app.include_router(llm_controller.get_router())
company_controller = CompanyController()
app.include_router(company_controller.get_router())
financial_data_controller = FinancialDataController()
app.include_router(financial_data_controller.get_router())
lstm_forecast_controller = LSTMForecastController()
app.include_router(lstm_forecast_controller.get_router())

# @app.on_event("startup")
# async def on_startup():
#     conf = ConfigService()
#     db = DBService(conf)
#     await db.init_db(Base)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)
