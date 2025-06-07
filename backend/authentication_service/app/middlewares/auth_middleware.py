from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from jose import jwt, JWTError
from app.core.config_service import get_config_service

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str, algorithm: str = "HS256"):
        super().__init__(app)
        self.secret_key = secret_key
        self.algorithm = algorithm

    async def dispatch(self, request: Request, call_next):
        request.state.user_email = None
        auth_header = request.headers.get("Authorization")
        print(auth_header)
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
                request.state.user_email = payload.get("sub")
            except JWTError as e:
                print(e)
                pass  # Не валидный токен — игнорируем

        response = await call_next(request)
        return response
