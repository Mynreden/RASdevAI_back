from fastapi import FastAPI, Request
import uvicorn
import os
from app.middlewares import register_middlewares
from dotenv import load_dotenv
from fastapi.dependencies.utils import solve_dependencies
from app.services import get_rabbit_service, RabbitService, get_email_sender_service, EmailSenderService
import asyncio
from contextlib import asynccontextmanager
from app.core import ConfigService
from app.database import get_db, get_db_service, DBService
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

@asynccontextmanager
async def lifespan(app: FastAPI):
    config_service = ConfigService()
    db_service = get_db_service(config_service=config_service)
    async for session in db_service.get_db():
        email_service = get_email_sender_service(config_service=config_service, db=session)
        rabbit_service =get_rabbit_service(config_service=config_service, email_sender_service=email_service)

        app.state.rabbit_service = rabbit_service

        consumer_task = asyncio.create_task(rabbit_service.start_consumer())
        print("✅ RabbitMQ consumer started")
    yield
    await rabbit_service.stop()
    consumer_task.cancel()
    print("🔌 RabbitMQ consumer stopped")

app = FastAPI(lifespan=lifespan, title="Email Service")

# midlewares regustration
register_middlewares(app)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Email service is running"}

@app.get("/metrics")
async def metrics(request: Request):
    rabbit_service: RabbitService = request.app.state.rabbit_service

    if rabbit_service and await rabbit_service.is_healthy():
        return {"rabbitmq": "connected"}
    return {"rabbitmq": "disconnected"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=True)
