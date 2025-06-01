from pydantic import BaseModel, Field
from .user import UserOut

class Token(BaseModel):
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(example="Bearer")
    user: UserOut  

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(description="Refresh token used to get a new access token")
