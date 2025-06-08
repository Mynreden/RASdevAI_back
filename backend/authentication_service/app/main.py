import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn
import os
from app.middlewares import register_middlewares
from app.controllers import AuthController, WatchlistController, PortfolioController, AlertController, StorageController
from app.database import get_db_service
from app.services import get_email_service, get_consumer_service, get_rabbit_manager, get_email_service, get_telegram_service
from dotenv import load_dotenv

from app.core import ConfigService, setup_custom_openapi, get_config_service

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config_service = get_config_service()
    rabbit_manager = get_rabbit_manager(config_service)
    email_service = get_email_service(rabbit_manager=rabbit_manager, config_service=config_service)
    telegram_service = get_telegram_service(rabbit_manager=rabbit_manager, config_service=config_service)
    db_service = get_db_service(config_service=config_service)
    consumer_service = get_consumer_service(rabbit_manager=rabbit_manager,
                                            email_service=email_service,
                                            telegram_service=telegram_service,
                                            config_service=config_service,
                                            db_service=db_service)
    consumer_task = asyncio.create_task(consumer_service.run())
    print("✅ RabbitMQ consumer started")

    yield

    await consumer_service.stop()
    consumer_task.cancel()
    print("🔌 RabbitMQ consumer stopped")


app = FastAPI(title="RASdevAI Auth Service", lifespan=lifespan)

register_middlewares(app)
setup_custom_openapi(app)


watchlist_controller = WatchlistController()
app.include_router(watchlist_controller.get_router())
auth_controller = AuthController()
app.include_router(auth_controller.get_router())  
portfolio_controller = PortfolioController()
app.include_router(portfolio_controller.get_router())  
alert_controller = AlertController()
app.include_router(alert_controller.get_router())  
storage_controller = StorageController()
app.include_router(storage_controller.get_router())  

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
