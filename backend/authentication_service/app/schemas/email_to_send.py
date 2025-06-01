from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class EmailToSend(BaseModel):
    email: EmailStr = Field(description="Email адрес получателя")
    subject: str = Field(min_length=1, max_length=255, description="Тема письма")
    body: str = Field(min_length=1, description="Текст письма (может быть plain text или HTML)")
    cc: Optional[list[EmailStr]] = Field(default=None, description="Копия письма (список email)")
    bcc: Optional[list[EmailStr]] = Field(default=None, description="Скрытая копия письма (список email)")
    attachments: Optional[list[str]] = Field(default=None, description="Список путей к вложениям или base64 (по желанию)")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "subject": "Пример письма",
                "body": "Здравствуйте! Это тестовое письмо.",
                "cc": ["manager@example.com"],
                "bcc": ["secret@example.com"],
                "attachments": ["path/to/file1.pdf", "path/to/file2.png"]
            }
        }
