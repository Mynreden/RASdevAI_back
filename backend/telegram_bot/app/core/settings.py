from pydantic import BaseSettings

class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    DATABASE_URL: str

    class Config:
        env_file = ".env"

settings = Settings()
