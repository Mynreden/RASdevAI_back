from redis.asyncio import Redis

class StubRedis:
    async def get(self, key: str):
        return None

    async def set(self, key: str, value: str):
        pass

    async def delete(self, key: str):
        pass

    async def aclose(self):
        pass
