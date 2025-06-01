import os
from starlette.config import Config

class ConfigService:
    def __init__(self):
        self.config = Config(environ=os.environ)
        
    def get(self, key: str, default=None):
        """Returns the value of a given config key."""
        return self.config(key, default=default)
    

_config_service_instance: ConfigService | None = None

def get_config_service() -> ConfigService:
    global _config_service_instance
    if _config_service_instance is None:
        _config_service_instance = ConfigService()
    return _config_service_instance