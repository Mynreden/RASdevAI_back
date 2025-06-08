from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    DATABASE_URL: str
    SERVICE_URL: str

    RABBIT_HOST: str
    RABBIT_PORT: int
    RABBIT_USERNAME: str 
    RABBIT_PASSWORD: str 
    RABBIT_TELEGRAM_QUEUE: str

    class Config:
        env_file = ".env"

settings = Settings()
