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

    def _key(self, predict_date: Optional[Union[str, date]] = None, ticker: Optional[str] = None,
            prefix: Optional[str] = "day", forecast: Optional[int] = None) -> str:
        date_str = (
            predict_date if isinstance(predict_date, str)
            else predict_date.isoformat() if predict_date
            else "*"
        )
        ticker_str = ticker.upper() if ticker else "*"
        prefix_str = prefix if prefix else "*"
        forecast_str = str(forecast) if forecast is not None else "*"
        
        return f"predictions:{prefix_str}:{date_str}:{ticker_str}:{forecast_str}"


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

    async def clear_predictions(self, ticker: Optional[str] = None, prefix: Optional[str] = None) -> int:
        pattern = self._key(predict_date=None, ticker=ticker, prefix=prefix, forecast=None)
        
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await self.redis.delete(*keys)
        return len(keys)
    
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
