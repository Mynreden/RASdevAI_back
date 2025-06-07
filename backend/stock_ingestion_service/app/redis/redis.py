from redis.asyncio import Redis
from redis.exceptions import RedisError
from typing import List, Optional, Union
from datetime import date
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


class PricePredictionRedis:
    def __init__(self, redis: TTLRedis):
        self.redis = redis

    def _key(self, predict_date: Union[str, date], ticker: str, prefix: str = "day", forecast: int = 1) -> str:
        date_str = predict_date if isinstance(predict_date, str) else predict_date.isoformat()
        return f"predictions:{prefix}:{date_str}:{ticker.upper()}:{forecast}"

    async def save_predictions(self, predict_date: date, ticker: str, prices: List[float], prefix="day", forecast: int = 1) -> None:
        key = self._key(predict_date, ticker, prefix=prefix, forecast=forecast)
        value = json.dumps(prices)
        await self.redis.set(key, value)

    async def get_predictions(self, predict_date: date, ticker: str, prefix="day", forecast: int = 1) -> Optional[List[float]]:
        key = self._key(predict_date, ticker, prefix=prefix, forecast=forecast)
        result = await self.redis.get(key)
        if result:
            return json.loads(result)
        return None

    async def close(self):
        await self.redis.aclose()


async def get_redis_client() -> PricePredictionRedis:
    config_service: ConfigService = get_config_service()

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

    return PricePredictionRedis(redis)
