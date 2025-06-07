from fastapi import APIRouter, Depends, HTTPException, Request
import openai
from collections import defaultdict
from ..core import get_config_service
from ..schemas import LLMPromptRequest

class LLMController:
    def __init__(self):
        self.router = APIRouter(prefix="/chat-gpt", tags=["chat-gpt"])
        self.client = openai.OpenAI(api_key=get_config_service().get("OPEN_AI_TOKEN", ""))
        self.user_histories = defaultdict(list)
        self.register_routes()

    def register_routes(self):
        @self.router.post("/", response_model=str)
        async def chat_with_gpt(request: LLMPromptRequest, http_request: Request):
            email = http_request.headers.get("X-User-Email", "anonymous")
            
            system_prompt = {
                "role": "system",
                "content": (
                    """You are an AI assistant for RASdevAI stock application. You are a financial expert assistant.
                IMPORTANT RULES:
                1. You MUST ONLY answer questions related to:
                - Stock market and trading
                - Financial analysis and investment
                - Portfolio management
                - Economic news and trends
                - Financial planning and advice
                - Cryptocurrency and digital assets
                - Banking and financial services
                - Market data interpretation

                2. For ANY question that is NOT related to finance, stocks, or economics, you MUST respond EXACTLY with:
                "I am an AI assistant specifically designed for RASdevAI stock application. I can only help with finance and stock-related questions."

                3. Always provide helpful, accurate financial information when the question is finance-related.
                4. If you're unsure whether a question is finance-related, err on the side of caution and use the standard response.

                Remember: You are part of the RASdevAI stock application ecosystem."""
                )
            }

            history = self.user_histories[email]
            if not history or history[0]["role"] != "system":
                history.insert(0, system_prompt)

            history.append({"role": "user", "content": request.message})

            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=history,
                    temperature=0.7,
                )
                reply = response.choices[0].message.content
                history.append({"role": "assistant", "content": reply})
                return reply
            except Exception as e:
                return f"❌ Ошибка при обращении к GPT: {str(e)}"

    def get_router(self):
        return self.router
