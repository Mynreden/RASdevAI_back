from fastapi import APIRouter, Depends, HTTPException, Query
import openai
from requests import request

from ..core import ConfigService, get_config_service
from ..services import NewsService, get_news_service
from ..schemas import NewsItem, LLMPromptRequest
from ..models import News

class LLMController:
    def __init__(self):
        self.router = APIRouter(prefix="/chat-gpt", tags=["chat-gpt"])
        self.client = openai.OpenAI(api_key=get_config_service().get("OPEN_AI_TOKEN", ""))
        self.register_routes()

    def register_routes(self):
        @self.router.post("/", response_model=str)
        async def get_all_news(
            request: LLMPromptRequest
        ):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Или "gpt-4", если у тебя есть доступ
                    messages=[
                        {"role": "user", "content": request.message}
                    ],
                    temperature=0.7,
                )
                reply = response.choices[0].message.content
                return reply
            except Exception as e:
                return f"❌ Ошибка при обращении к GPT: {str(e)}"
            
            
    def get_router(self):
        return self.router
