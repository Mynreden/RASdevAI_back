from pydantic import BaseModel, EmailStr, constr, Field
from typing import Annotated
from pydantic import StringConstraints

Username = Annotated[str, StringConstraints(min_length=3, strip_whitespace=True)]
Password = Annotated[str, StringConstraints(min_length=8)]

class UserCreate(BaseModel):
    username: Username = Field(min_length=3, strip_whitespace=True, description="Unique username")
    email: EmailStr = Field(description="User email")
    password: Password = Field(min_length=8, description="Password (min 8 characters)")

class UserOut(BaseModel):
    id: int = Field(example=1)
    username: str = Field(example="john_doe")
    email: EmailStr = Field(example="john@example.com")
    auth_provider: str = Field(example="google", description="OAuth provider or 'local'")
    is_active: bool = Field(example=True)

    class Config:
        from_attributes = True

class PasswordChange(BaseModel):
    old_password: str = Field(min_length=8, description="Current password")
    new_password: str = Field(min_length=8, description="New password")

class LoginRequest(BaseModel):
    email: EmailStr = Field(description="User email")
    password: Password = Field(min_length=8, description="Password (min 8 characters)")
