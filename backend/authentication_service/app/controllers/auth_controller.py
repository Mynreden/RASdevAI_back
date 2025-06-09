from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Query
from fastapi.responses import HTMLResponse
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core import get_config_service, ConfigService
from app.services import AuthService, EmailService, OAuthService,  get_auth_service, get_email_service, get_oauth_service
from app.schemas import UserCreate, Token, PasswordChange, RefreshTokenRequest, LoginRequest, TelegramLoginRequest
import logging
from typing import Dict
from starlette.datastructures import URL
import qrcode
import io
from datetime import datetime, timedelta
from jose import jwt, JWTError
from sqlalchemy import select
from ..models import User
from ..redis import TTLRedis, get_redis_client
import uuid


class AuthController:
    def __init__(self):
        self.router = APIRouter(prefix="/auth", tags=["auth"])
        self.register_routes()

    def register_routes(self):
        @self.router.post("/register")
        async def register(user: UserCreate, 
                           db: AsyncSession = Depends(get_db),             
                           auth_service: AuthService = Depends(get_auth_service),
                           email_service: EmailService = Depends(get_email_service),
                           config_service: ConfigService = Depends(get_config_service)):
            user_data = await auth_service.register_user(user)
            verification_token = auth_service.create_verification_token({"user_id": user_data["user_id"]})
            verification_url = config_service.get("GATEWAY_URL", "")
            verification_link = f"{verification_url}/api/auth/verify-email?token={verification_token}"
            await email_service.send_verification_email(user_data["email"], verification_link)
            return {"message": "User registered successfully"}

        @self.router.get("/verify-email")
        async def verify_email(token: str, 
                               db: AsyncSession = Depends(get_db),                           
                               auth_service: AuthService = Depends(get_auth_service)):
            return await auth_service.verify_email(token)

        @self.router.post("/login", response_model=Token)
        async def login(request: LoginRequest = Body(...), 
                        db: AsyncSession = Depends(get_db),                           
                        auth_service: AuthService = Depends(get_auth_service)):
            email = request.email
            password = request.password
            if not email or not password:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and password required")
            return await auth_service.login_user(email, password)

        @self.router.post("/refresh", response_model=Token)
        async def refresh_token(payload: RefreshTokenRequest,                           
                                auth_service: AuthService = Depends(get_auth_service)):
            return await auth_service.refresh_token(payload.refresh_token)

        @self.router.post("/change-password")
        async def change_password(data: PasswordChange, 
                                  request: Request, 
                                  db: AsyncSession = Depends(get_db),                           
                                  auth_service: AuthService = Depends(get_auth_service)):
            email = request.state.user_email
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
            return await auth_service.change_password(email, data.old_password, data.new_password)
        
        @self.router.post("/telegram_login")
        async def telegram_login(request: TelegramLoginRequest = Body(...), 
                        db: AsyncSession = Depends(get_db),                           
                        auth_service: AuthService = Depends(get_auth_service)) -> Token:
            email = request.email
            password = request.password
            telegram_id = request.telegram_id
            if not email or not password or not telegram_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email, password and telegram_id required")
            return await auth_service.telegram_login(email, password, telegram_id)

        @self.router.get("/telegram-qr")
        async def generate_telegram_qr(config_service: ConfigService = Depends(get_config_service), 
                                       request: Request = None,
                                        redis: TTLRedis = Depends(get_redis_client)):
            email: str = request.state.user_email
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not authenticated"
                )
            secret_key = config_service.get("SECRET_KEY")
            bot_username = config_service.get("TELEGRAM_BOT_USERNAME", "RASdevAI_SA_bot")

            payload = {
                "sub": email,
                "exp": datetime.utcnow() + timedelta(hours=1)
            }
            token = jwt.encode(payload, secret_key, algorithm="HS256")

            session_code = uuid.uuid4().hex[:8]
            await redis.set(session_code, token)

            tg_link = f"t.me/{bot_username}?start={session_code}"

            img = qrcode.make(tg_link, version=None, error_correction=qrcode.constants.ERROR_CORRECT_M)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            return StreamingResponse(buffer, media_type="image/png")

        @self.router.get("/telegram-qr-login")
        async def login_telegram_qr(token: str = Query(...),
                                    telegram_id: int = Query(...),
                                    config_service: ConfigService = Depends(get_config_service),     
                                    db: AsyncSession = Depends(get_db),
                                    redis: TTLRedis = Depends(get_redis_client)):
            secret_key = config_service.get("SECRET_KEY")

            try:
                token_code = await redis.get(token)
                payload = jwt.decode(token_code, secret_key, algorithms=["HS256"])
                email = payload.get("sub")
                if not email:
                    raise HTTPException(status_code=400, detail="Invalid token: no email")

                result = await db.execute(select(User).where(User.email == email))
                user = result.scalars().first()

                if not user:
                    raise HTTPException(status_code=404, detail="User not found")

                user.telegram_id = telegram_id
                db.add(user)
                await db.commit()

                return "Telegram ID linked successfully"
            except JWTError:
                raise HTTPException(status_code=400, detail="Invalid token")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
        
        @self.router.get("/login/google")
        async def google_login(request: Request,
                               oauth_service: OAuthService = Depends(get_oauth_service),
                               config_service: ConfigService = Depends(get_config_service)):
            redirect_uri = URL(str(config_service.get("GATEWAY_URL")) + "/api/auth/google")  # request.url_for("google_callback")
            return await oauth_service.get_oauth().google.authorize_redirect(request, redirect_uri, access_type="offline", prompt="consent")

        @self.router.get("/google", name="google_callback")
        async def google_callback(request: Request, 
                                  db: AsyncSession = Depends(get_db),                           
                                  auth_service: AuthService = Depends(get_auth_service),
                                  oauth_service: OAuthService = Depends(get_oauth_service)):
            try:
                oauth = oauth_service.get_oauth()
                token = await oauth.google.authorize_access_token(request)
                user_info = await oauth.google.userinfo(token=token)
            except Exception as e:
                logging.error(f"Error during Google OAuth callback: {e}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"OAuth error: {e}")

            token_response = await auth_service.handle_google_login(user_info)
            return HTMLResponse(
                f"""
                <script>
                    window.opener.postMessage({{
                        message: 'Google login successful',
                        access_token: '{token_response.access_token}',
                        refresh_token: '{token_response.refresh_token}',
                        token_type: 'bearer',
                        user_info: {{
                            'username': '{user_info.get("name")}',
                            'given_name': '{user_info.get("given_name")}',
                            'family_name': '{user_info.get("family_name")}',
                            'picture': '{user_info.get("picture")}',
                            'email': '{user_info.get("email")}',
                        }},
                    }}, '*');
                    window.close();
                </script>
                """
            )

        @self.router.get("/user-info")
        async def user_info(request: Request,
                            db: AsyncSession = Depends(get_db),
                            auth_service: AuthService = Depends(get_auth_service)):
            email = request.state.user_email
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
            user_info = await auth_service.get_user_info(email)
            if not user_info:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            return user_info

    def get_router(self):
        return self.router