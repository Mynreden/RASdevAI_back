from redis.asyncio import Redis
from redis.exceptions import RedisError
from fastapi import Depends
from typing import AsyncGenerator

from .stub_redis import StubRedis
from ..core import get_config_service, ConfigService


class TTLRedis(Redis):
    def __init__(self, *args, default_ttl=3600, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_ttl = default_ttl

    async def set(self, name, value, ex=None, *args, **kwargs):
        if ex is None:
            ex = self.default_ttl
        return await super().set(name, value, ex=ex, *args, **kwargs)

async def get_redis_client(
    config_service: ConfigService = Depends(get_config_service)
) -> AsyncGenerator[Redis, None]:
    try:
        client = TTLRedis(
            host=config_service.get("REDIS_HOST", "localhost"),
            port=int(config_service.get("REDIS_PORT", 6379)),
            username=config_service.get("REDIS_USERNAME", "default"),
            password=config_service.get("REDIS_PASSWORD", None),
            decode_responses=True,
            default_ttl=int(config_service.get("REDIS_CACHE_EXPIRE_SECONDS", 3600)),
        )

        await client.ping()
        yield client
        await client.aclose()
    except RedisError:
        yield StubRedis()
