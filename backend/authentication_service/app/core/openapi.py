# app/core/openapi.py

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def setup_custom_openapi(app: FastAPI):
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="User Service",
            version="1.0.0",
            description="API with JWT authentication",
            routes=app.routes,
        )
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
        for path in openapi_schema["paths"].values():
            for method in path.values():
                method.setdefault("security", []).append({"BearerAuth": []})
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
