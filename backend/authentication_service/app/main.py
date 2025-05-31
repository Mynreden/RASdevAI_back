import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn
import os
from app.middlewares import register_middlewares
from app.controllers import AuthController, WatchlistController, PortfolioController
from app.services import get_email_service
from dotenv import load_dotenv

from app.core import ConfigService

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config_service = ConfigService()
    email_service = get_email_service(config_service=config_service)

    app.state.email_service = email_service

    consumer_task = asyncio.create_task(email_service.connect())
    print("✅ RabbitMQ consumer started")

    yield

    await email_service.close()
    consumer_task.cancel()
    print("🔌 RabbitMQ consumer stopped")


app = FastAPI(title="RASdevAI Auth Service", lifespan=lifespan)

# midlewares regustration
register_middlewares(app)

# controller registratiom
watchlist_controller = WatchlistController()
app.include_router(watchlist_controller.get_router())  #
auth_controller = AuthController()
app.include_router(auth_controller.get_router())  
portfolio_controller = PortfolioController()
app.include_router(portfolio_controller.get_router())  


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
