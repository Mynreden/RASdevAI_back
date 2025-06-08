import aio_pika
from fastapi import Depends
from ..core import ConfigService, get_config_service

class RabbitMQManager:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.abc.AbstractChannel | None = None

    async def connect(self):
        if not self.connection or self.connection.is_closed:
            self.connection = await aio_pika.connect_robust(
                host=self.host,
                port=self.port,
                login=self.username,
                password=self.password
            )
            self.channel = await self.connection.channel()
            print("✅ RabbitMQManager: Connected")

    async def get_channel(self):
        if not self.channel:
            await self.connect()
        return self.channel

    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            print("🔌 RabbitMQManager: Connection closed")

_rabbit_manager_singleton: RabbitMQManager | None = None

def get_rabbit_manager(config_service: ConfigService = Depends(get_config_service)) -> RabbitMQManager:
    global _rabbit_manager_singleton
    if _rabbit_manager_singleton is None:
        _rabbit_manager_singleton = RabbitMQManager(
            host=config_service.get("RABBIT_HOST"),
            port=int(config_service.get("RABBIT_PORT")),
            username=config_service.get("RABBIT_USER"),
            password=config_service.get("RABBIT_PASS"),
        )
    return _rabbit_manager_singleton