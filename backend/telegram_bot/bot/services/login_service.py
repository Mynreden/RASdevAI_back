from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..config import settings
import httpx

class LoginService:
    def __init__(self):
        self.auth_service_url = settings.SERVICE_URL

    async def login_user(self, email: str, password: str, telegram_id: int) -> bool:
        url = f"{self.auth_service_url}/api/auth/telegram_login"
        payload = {
            "email": email,
            "password": password,
            "telegram_id": telegram_id
        }
        print("Payload:", payload)
        print("URL:", url)
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"accept": "application/json", "Content-Type": "application/json"}
                )
                print("Status Code:", response.status_code)
                print("Response Body:", response.text)
                return response.status_code == 200
            except httpx.RequestError as e:
                print("Request failed:", repr(e))
                return False
