from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class TelegramToSend(BaseModel):
    chat_id: int = Field(description="ID получателя")
    text: str = Field(min_length=1, description="Текст письма")