# middleware/error_handler.py

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import traceback
from ..core import logger

class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            traceback_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            logger.error("Unhandled exception:\n%s", traceback_str)

            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error": str(exc)
                }
            )
