import uuid
from fastapi import APIRouter, UploadFile, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..core import ConfigService, get_config_service
from ..services import StorageService, get_storage_service
from ..database import get_db
from ..models import User 

class StorageController:
    def __init__(self):
        self.router = APIRouter(prefix="/storage", tags=["storage"])
        self.register_routes()

    def register_routes(self):
        @self.router.post("/upload")
        async def upload_file(
            file: UploadFile,
            storage_service: StorageService = Depends(get_storage_service)
        ):
            file_uuid = uuid.uuid4()
            result = await storage_service.save_file(file_uuid, file)
            return result

        @self.router.get("/file/{file_uuid}")
        async def get_file_url(
            file_uuid: uuid.UUID,
            storage_service: StorageService = Depends(get_storage_service)
        ):
            url = storage_service.get_file_url(file_uuid)
            return {"uuid": str(file_uuid), "url": url}

        @self.router.delete("/file/{file_uuid}")
        async def delete_file(
            file_uuid: uuid.UUID,
            storage_service: StorageService = Depends(get_storage_service)
        ):
            result = storage_service.delete_file(file_uuid)
            return result

        @self.router.post("/upload-profile-pic")
        async def upload_profile_pic(
            request: Request,
            file: UploadFile,
            db: AsyncSession = Depends(get_db),
            storage_service: StorageService = Depends(get_storage_service)
        ):
            # Получаем email текущего пользователя из middleware (request.state.user_email)
            email = request.state.user_email
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

            # Ищем пользователя в базе
            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            # Генерируем UUID и сохраняем файл в Spaces
            file_uuid = uuid.uuid4()
            save_result = await storage_service.save_file(file_uuid, file)
            file_url = save_result["url"]

            # Обновляем profile_pic пользователя в базе на URL загруженного файла
            stmt = update(User).where(User.id == user.id).values(profile_pic=file_url)
            await db.execute(stmt)
            await db.commit()

            return {"message": "Profile picture updated", "url": file_url}

        @self.router.get("/profile-pic")
        async def get_profile_pic(
            request: Request,
            db: AsyncSession = Depends(get_db)
        ):
            email = request.state.user_email
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalars().first()
            if not user or not user.profile_pic:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile picture not found")

            return {"url": user.profile_pic}

        @self.router.delete("/profile-pic")
        async def delete_profile_pic(
            request: Request,
            db: AsyncSession = Depends(get_db),
            storage_service: StorageService = Depends(get_storage_service)
        ):
            email = request.state.user_email
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

            # Получаем пользователя
            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalars().first()
            if not user or not user.profile_pic:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile picture not found")

            # Парсим UUID из URL (предполагая, что URL формата https://space.region.digitaloceanspaces.com/path/{uuid}.{ext})
            # Можно более надежно, но для примера:
            import re
            match = re.search(r'/([0-9a-fA-F-]{36})\.', user.profile_pic)
            if not match:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid profile picture URL format")

            file_uuid = uuid.UUID(match.group(1))

            # Удаляем файл из storage
            storage_service.delete_file(file_uuid)

            # Обнуляем поле profile_pic в базе
            stmt = update(User).where(User.id == user.id).values(profile_pic=None)
            await db.execute(stmt)
            await db.commit()

            return {"message": "Profile picture deleted"}

    def get_router(self):
        return self.router
