# app/middleware.py
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from app.core.config_service import get_config_service
from .error_handler import ExceptionMiddleware
from .auth_middleware import AuthMiddleware

def register_middlewares(app: FastAPI):
    config = get_config_service()
    secret_key = config.get("SECRET_KEY")

    app.add_middleware(SessionMiddleware, secret_key=secret_key)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
   # app.add_middleware(ExceptionMiddleware)
    app.add_middleware(AuthMiddleware, secret_key=secret_key)

