import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models import User
from app.schemas import UserCreate, Token, PasswordChange, RefreshTokenRequest, UserOut
from fastapi import Depends

from ..core import ConfigService, get_config_service
from ..database import get_db

class AuthService:
    def __init__(self, config_service, db: AsyncSession):
        self.config_service = config_service
        self.SECRET_KEY = self.config_service.get("SECRET_KEY")
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY is required")
        self.VERIFICATION_SECRET_KEY = self.config_service.get("VERIFICATION_SECRET_KEY")
        if not self.VERIFICATION_SECRET_KEY:
            raise ValueError("VERIFICATION_SECRET_KEY is required")
        self.ALGORITHM = "HS256"
        self.VERIFICATION_TOKEN_EXPIRE_MINUTES = 60
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 60
        self.REFRESH_TOKEN_EXPIRE_DAYS = 7
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.db = db

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def create_refresh_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS))
        to_encode.update({"exp": expire, "token_type": "refresh"})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def create_verification_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=self.VERIFICATION_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.VERIFICATION_SECRET_KEY, algorithm=self.ALGORITHM)

    async def register_user(self, user: UserCreate) -> Dict:
        result = await self.db.execute(select(User).where(User.email == user.email))
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        hashed_pwd = self.get_password_hash(user.password)
        new_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_pwd,
            auth_provider="local",
            email_verified=False,
            profile_pic="https://rasdevai.fra1.cdn.digitaloceanspaces.com/users/default_profile_image.jpg"
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return {"user_id": new_user.id, "email": new_user.email}

    async def verify_email(self, token: str) -> Dict:
        try:
            payload = jwt.decode(token, self.VERIFICATION_SECRET_KEY, algorithms=[self.ALGORITHM])
            user_id: int = payload.get("user_id")
            if user_id is None:
                raise HTTPException(status_code=400, detail="Invalid verification token")
        except JWTError:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.email_verified = True
        await self.db.commit()
        return {"message": "Email verified successfully"}

    async def login_user(self, email: str, password: str) -> Token:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user or not user.hashed_password or not self.verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.email_verified:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified")

        access_token = self.create_access_token({"sub": user.email})
        refresh_token = self.create_refresh_token({"sub": user.email})
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer", user=user)
    
    async def telegram_login(self, email: str, password: str, telegram_id: int) -> Token:
        token = await self.login_user(email=email, password=password)
        result = await self.db.execute(select(User).where(User.id == token.user.id))
        user = result.scalars().first()
        user.telegram_id = telegram_id
        self.db.add(user)
        await self.db.commit()
        return token

    async def refresh_token(self, refresh_token: str) -> Token:
        try:
            token_data = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if token_data.get("token_type") != "refresh":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
            email = token_data.get("sub")
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        new_access_token = self.create_access_token({"sub": email})
        new_refresh_token = self.create_refresh_token({"sub": email})
        return Token(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")

    async def change_password(self, email: str, old_password: str, new_password: str) -> Dict:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user or not user.hashed_password or not self.verify_password(old_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Old password is incorrect")

        user.hashed_password = self.get_password_hash(new_password)
        await self.db.commit()
        return {"message": "Password changed successfully"}

    async def handle_google_login(self, user_info: Dict) -> Token:
        email = user_info.get("email")
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No email provided by Google")

        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user:
            user = User(
                username=user_info.get("name") or email.split("@")[0],
                email=email,
                hashed_password=None,
                auth_provider="google",
                email_verified=True,
                social_id=user_info.get("sub"),
                profile_pic=user_info.get("picture")
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

        access_token = self.create_access_token({"sub": user.email})
        refresh_token = self.create_refresh_token({"sub": user.email})
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer", user=UserOut(id=user.id, 
                                                                                                               username=user.username, 
                                                                                                               email=email,
                                                                                                               auth_provider=user.auth_provider, 
                                                                                                               is_active=user.is_active, 
                                                                                                               profile_pic=user.profile_pic,
                                                                                                               subscription_type=user.subscription_type))
    

def get_auth_service(config_service: ConfigService = Depends(get_config_service), 
                    db: AsyncSession = Depends(get_db)) -> AuthService:
    """Функция зависимости для предоставления экземпляра AuthService."""
    return AuthService(config_service=config_service, db=db)
