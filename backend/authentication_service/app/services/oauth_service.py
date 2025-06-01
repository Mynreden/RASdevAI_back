from authlib.integrations.starlette_client import OAuth
from fastapi import Depends
from ..core import ConfigService, get_config_service

class OAuthService:
    def __init__(self, config_service: ConfigService):
        self.config = config_service
        self.oauth = OAuth(self.config)
        self._register_oauth_providers()

    def _register_oauth_providers(self):
        """Register all oauth providers."""
        self.oauth.register(
            name="google",
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )

    def get_oauth(self):
        """Returns the oauth instance."""
        return self.oauth
    
def get_oauth_service(config_service: ConfigService = Depends(get_config_service)) -> OAuthService:
    """Функция зависимости для предоставления экземпляра OAuthService."""
    return OAuthService(config_service=config_service)

