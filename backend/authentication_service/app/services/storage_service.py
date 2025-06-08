import uuid
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status, Depends
from botocore.client import Config
import boto3
from ..core import ConfigService, get_config_service
import os

class StorageService:
    # Можно менять этот список расширений по своему усмотрению
    ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".pdf", ".txt", ".json", ".csv", ".mp4", ".mp3", ""]

    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
        self.space_name = self.config_service.get("SPACE_NAME")
        self.region = self.config_service.get("SPACE_REGION", "fra1")
        self.base_path = self.config_service.get("SPACE_BASE_PATH", "users/").rstrip("/") + "/"

        self.client = boto3.client(
            's3',
            region_name=self.region,
            endpoint_url=f"https://{self.region}.digitaloceanspaces.com",
            aws_access_key_id=self.config_service.get("SPACE_ACCESS_KEY"),
            aws_secret_access_key=self.config_service.get("SPACE_SECRET_KEY"),
            config=Config(signature_version='s3v4')
        )

    async def save_file(self, file_uuid: uuid.UUID, file: UploadFile) -> dict:
        ext = os.path.splitext(file.filename)[1].lower()  # Получаем расширение из имени файла
        key = f"{self.base_path}{file_uuid}{ext}"

        try:
            self.client.put_object(
                Bucket=self.space_name,
                Key=key,
                Body=file.file,
                ACL='public-read',
                ContentType=file.content_type
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        return {"message": "File saved", "uuid": str(file_uuid), "url": self.get_file_url(file_uuid)}

    def find_file_key(self, file_uuid: uuid.UUID) -> Optional[str]:
        """
        Перебирает расширения и возвращает первый существующий ключ
        """
        for ext in self.ALLOWED_EXTENSIONS:
            key = f"{self.base_path}{file_uuid}{ext}"
            try:
                self.client.head_object(Bucket=self.space_name, Key=key)
                return key
            except self.client.exceptions.NoSuchKey:
                continue
            except Exception:
                # Пробрасываем остальные ошибки
                raise

        return None

    def get_file_url(self, file_uuid: uuid.UUID) -> str:
        key = self.find_file_key(file_uuid)
        if not key:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

        return f"https://{self.space_name}.{self.region}.digitaloceanspaces.com/{key}"

    def delete_file(self, file_uuid: uuid.UUID) -> dict:
        key = self.find_file_key(file_uuid)
        if not key:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

        try:
            self.client.delete_object(Bucket=self.space_name, Key=key)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        return {"message": "File deleted", "uuid": str(file_uuid)}

def get_storage_service(config_service: ConfigService = Depends(get_config_service)) -> StorageService:
    return StorageService(config_service=config_service)
