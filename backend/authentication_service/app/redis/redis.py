from redis.asyncio import Redis
from redis.exceptions import RedisError
from typing import List, Optional, Union
from datetime import date
from fastapi import Depends

import json

from ..core import get_config_service, ConfigService


class TTLRedis(Redis):
    def __init__(self, *args, default_ttl=3600, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_ttl = default_ttl

    async def set(self, name, value, ex=None, *args, **kwargs):
        if ex is None:
            ex = self.default_ttl
        return await super().set(name, value, ex=ex, *args, **kwargs)



async def get_redis_client(config_service: ConfigService = Depends(get_config_service)) -> TTLRedis:

    redis = TTLRedis(
        host=config_service.get("REDIS_HOST", "localhost"),
        port=int(config_service.get("REDIS_PORT", 6379)),
        decode_responses=True,
        default_ttl=int(config_service.get("REDIS_CACHE_EXPIRE_SECONDS", 3600)),
    )

    try:
        await redis.ping()
    except RedisError as e:
        raise RuntimeError("Failed to connect to Redis") from e

    return redis
