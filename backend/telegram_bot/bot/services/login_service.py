from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from bot.models import User  # импорт твоей модели User

class LoginService:
    def __init__(self, db: AsyncSession):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.db = db

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        print(f"Hashed: {hashed_password}")
        print(f"Plain: {plain_password}")
        return self.pwd_context.verify(plain_password, hashed_password)

    async def login_user(self, email: str, password: str) -> User:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user or not user.hashed_password or not self.verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.email_verified:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified")
        return user
