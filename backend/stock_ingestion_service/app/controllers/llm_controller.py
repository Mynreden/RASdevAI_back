from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Optional
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
from sqlalchemy.orm import aliased
import openai
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from ..database import get_db
from ..core import get_config_service
from ..schemas import LLMPromptRequest, RecentCompanyDataResponse, FinancialDataItem, NewsItem, StockResponse, MiniChartData
from ..redis import PricePredictionRedis, get_redis_client
from ..models import Company, FinancialData, News, StockPrice

class LLMController:
    def __init__(self):
        self.router = APIRouter(prefix="/chat-gpt", tags=["chat-gpt"])
        self.client = openai.OpenAI(api_key=get_config_service().get("OPEN_AI_TOKEN", ""))
        self.register_routes()

    def register_routes(self):
        @self.router.post("/", response_model=str)
        async def chat_with_gpt(request: LLMPromptRequest, http_request: Request,
                redis: PricePredictionRedis = Depends(get_redis_client),
                db: AsyncSession = Depends(get_db)):
            email = http_request.state.user_email
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

            history = await self.load_history(email, redis)
            print("History: ", history)
            if not history or history[0]["role"] != "system":
                company_ticker = await self.extract_company_ticker(request.message, db)
                print(company_ticker)
                company_data = None
                if company_ticker:
                    company_data = await self.get_recent_data(company_ticker, db)

                system_prompt = self.build_system_prompt(company_data)
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

                await self.save_history(email, history, redis)

                return reply
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ошибка при обращении к GPT: {str(e)}")
    
        @self.router.delete("/refresh", response_model=dict)
        async def refresh_history(http_request: Request, redis: PricePredictionRedis = Depends(get_redis_client)):
            email = http_request.state.user_email
            if not email:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

            try:
                await redis.redis.delete(f"user_history:{email}")
                return {"detail": "История успешно сброшена"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ошибка при сбросе истории: {str(e)}")


    async def load_history(self, user_email: str,
                redis: PricePredictionRedis = Depends(get_redis_client)) -> list:
        raw = await redis.redis.get(f"user_history:{user_email}")
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return []
        return []

    async def save_history(self, user_email: str, history: list,
                redis: PricePredictionRedis = Depends(get_redis_client)):
        await redis.redis.set(f"user_history:{user_email}", json.dumps(history), ex=3600)

    async def extract_company_ticker(self, user_message: str, db: AsyncSession) -> Optional[str]:
        try:
            # 1. Загружаем компании из БД
            result = await db.execute(select(Company).where(Company.is_deleted == False))
            companies = result.scalars().all()
            if not companies:
                return None

            # 2. Формируем список названий компаний
            company_names = [f"{c.ticker} - {c.shortname}" for c in companies]
            system_prompt = {
                "role": "system",
                "content": (
                    "Ты — финансовый помощник. Я дам тебе список компаний и пользовательский вопрос. "
                    "Твоя задача — выбрать ОДНУ компанию из списка, к которой относится вопрос. "
                    "Если ни одна из компаний не подходит, ответь точно: 'None'. "
                    "Возвращай ТОЛЬКО тикер компании ИЗ списка, без пояснений. Если не уверен — пиши 'None'."
                ),
            }
            user_prompt = {
                "role": "user",
                "content": (
                    f"Список компаний:\n{', '.join(company_names)}\n\n"
                    f"Вопрос пользователя:\n{user_message}"
                ),
            }
            # 3. GPT определяет компанию
            print(system_prompt, user_prompt)
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[system_prompt, user_prompt],
                temperature=0.0,
            )
            reply = response.choices[0].message.content.strip()
            print(f"LLM determined context: {reply}")
            if reply == "None":
                return None
            matched = next((c for c in companies if c.ticker.lower() == reply.lower()), None)
            return matched.ticker if matched else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error determining company from user message: {str(e)}")

    async def get_recent_data(self, company_ticker: str, db: AsyncSession) -> dict:
        try:
            one_month_ago = datetime.today() - timedelta(days=10)
            company = (await db.execute(
                select(Company)
                .where(
                    Company.ticker == company_ticker,
                )
            )).scalar()

            financial_stmt = (
                select(FinancialData)
                .where(
                    FinancialData.ticker == company_ticker,
                )
                .order_by(FinancialData.change_date.desc())
                .limit(4)
            )
            financial_result = await db.execute(financial_stmt)
            financial_data = financial_result.scalars().all()


            # Цены акций
            stock_stmt = (
                select(StockPrice)
                .where(
                    StockPrice.ticker == company_ticker,
                    StockPrice.date >= one_month_ago.date()
                )
                .order_by(StockPrice.date.desc())
            )
            stock_result = await db.execute(stock_stmt)
            stock_data = stock_result.scalars().all()

            # Преобразование stock_data в StockResponse (берём последние цены и создаём мини-график)
            if stock_data:
                price_data = [
                    MiniChartData(
                        date=sp.date.strftime("%Y-%m-%d"),
                        value=sp.close
                    )
                    for sp in reversed(stock_data)  # чтобы данные шли по возрастанию даты
                ]

                stock_response = StockResponse(
                    logoUrl=company.image_url or "",
                    companyName=company.shortname,
                    ticker=company.ticker,
                    shareChange=((stock_data[0].close - stock_data[-1].close) / stock_data[-1].close) * 100,
                    currentPrice=stock_data[0].close,
                    priceData=price_data,
                )
            else:
                stock_response = None

            # Ответ
            return RecentCompanyDataResponse(
                financial_data=[FinancialDataItem.from_orm(financial) for financial in financial_data],
                news=[NewsItem.from_orm(news) for news in []],
                stock=stock_response
            )
        

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при получении данных по компании: {str(e)}")


    def build_system_prompt(self, company_data: Optional[RecentCompanyDataResponse]) -> dict:
        base_content = (
            "You are an AI assistant for RASdevAI stock application. You are a financial expert assistant.\n"
            "IMPORTANT RULES:\n"
            "1. You MUST ONLY answer questions related to:\n"
            "- Stock market and trading\n"
            "- Financial analysis and investment\n"
            "- Portfolio management\n"
            "- Economic news and trends\n"
            "- Financial planning and advice\n"
            "- Cryptocurrency and digital assets\n"
            "- Banking and financial services\n"
            "- Market data interpretation\n\n"
            "2. For ANY question that is NOT related to finance, stocks, or economics, you MUST respond EXACTLY with:\n"
            "\"I am an AI assistant specifically designed for RASdevAI stock application. I can only help with finance and stock-related questions.\"\n\n"
            "3. Always provide helpful, accurate financial information when the question is finance-related.\n"
            "4. If you're unsure whether a question is finance-related, err on the side of caution and use the standard response.\n\n"
            "STYLE AND FORMAT RULES:\n"
            "- Be brief and to the point (no long generic text).\n"
            "- Give a clear, simple financial opinion or recommendation.\n"
            "- Highlight key financial metrics only if relevant to the question.\n"
            "- Avoid repeating obvious or general advice.\n"
            "- Write in a natural and confident tone.\n\n"
            "Remember: You are part of the RASdevAI stock application ecosystem."
        )
        base_content += (
            "\n\nYou should behave like a real financial analyst. When asked if buying a stock is a good idea, always analyze:\n"
            "- Whether the company is fundamentally strong\n"
            "- Its current market trend\n"
            "- Key financial ratios (like ROE, ROA)\n"
            "- Risks and opportunities\n"
            "Then give a brief summary and a **suggestion** whether it could be a reasonable investment or not."
        )

        if company_data:
            base_content += f"\n\nRecent data for company:\n{self.make_readable_text(company_data)}"
        print(base_content)

        return {"role": "system", "content": base_content}

    def get_router(self):
        return self.router
    
    def make_readable_text(self, data: BaseModel) -> str:
        info = data.model_dump()
        output = []
        for key, value in info.items():
            readable_key = key.replace("_", " ").capitalize()
            output.append(f"- {readable_key}: {value}")
        return "\n".join(output)
