from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import traceback

from bot.schemas import StockResponse
from bot.services import LoginService, StockService  # добавил StockService из предыдущего ответа

class LoginStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()

class BotHandler:
    def __init__(self):
        self.router = Router()
        self.login_service = LoginService()
        self.stock_service = StockService()

        # Регистрируем все обработчики
        self.router.message.register(self.start_handler, F.text.startswith("/start"))
        self.router.message.register(self.start_handler, F.text.startswith("/login"))

        self.router.message.register(self.email_entered, LoginStates.waiting_for_email)
        self.router.message.register(self.password_entered, LoginStates.waiting_for_password)

        self.router.callback_query.register(self.show_companies, F.data == "menu_companies")
        self.router.callback_query.register(self.company_actions, F.data.startswith("company_"))
        self.router.callback_query.register(self.show_news, F.data.startswith("news_"))
        self.router.callback_query.register(self.show_main_menu, F.data == "menu_main")
        self.router.callback_query.register(self.show_forecast, F.data.startswith("forecast_"))
        self.router.callback_query.register(self.show_price_history, F.data.startswith("history_"))


    async def start_handler(self, message: Message, state: FSMContext):
        print(message.text)
        parts = message.text.split(" ", 1)
        if len(parts) == 1:
            await message.answer("Введите email:")
            await state.set_state(LoginStates.waiting_for_email)
        else:
            token = parts[1]
            telegram_id = message.from_user.id
            success = await self.login_service.login_with_token(token, telegram_id)
            if success:
                await message.answer("Успешный вход через QR-token 🎉", reply_markup=self.main_menu())
            else:
                await message.answer("Неверный или просроченный токен ❌")

    async def email_entered(self, message: Message, state: FSMContext):
        await state.update_data(email=message.text)
        await message.answer("Введите пароль:")
        await state.set_state(LoginStates.waiting_for_password)

    async def password_entered(self, message: Message, state: FSMContext):
        data = await state.get_data()
        email = data.get("email")
        password = message.text
        telegram_id = message.from_user.id

        try:
            is_success = await self.login_service.login_user(email, password, telegram_id)
            if is_success:
                await message.answer(
                    "Успешный вход. Telegram ID привязан.\n\nВыберите действие:",
                    reply_markup=self.main_menu()
                )
                await state.clear()
            else:
                await message.answer("Неверные данные или email не подтверждён.")
        except Exception as e:
            await message.answer("Произошла неизвестная ошибка")
            await state.clear()
            traceback.print_exc()
            print(e)

    def main_menu(self):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Активные компании", callback_data="menu_companies")]
        ])
        return keyboard

    async def show_companies(self, callback: CallbackQuery):
        companies = await self.stock_service.get_companies()

        if not companies:
            await callback.answer("Не удалось получить список компаний.", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=company.shortname, callback_data=f"company_{company.ticker}")]
                for company in companies
            ]
        )
        await callback.message.edit_text("Выберите компанию:", reply_markup=keyboard)

    async def company_actions(self, callback: CallbackQuery):
        ticker = callback.data.split("_", 1)[1]

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📉 Прогноз на неделю", callback_data=f"forecast_{ticker}")],
            [InlineKeyboardButton(text="📰 Последние новости", callback_data=f"news_{ticker}_0")],
            [InlineKeyboardButton(text="💹 История цен", callback_data=f"history_{ticker}")],
            [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu_main")]
        ])

        await callback.message.edit_text(f"Вы выбрали компанию {ticker}. Что хотите посмотреть?", reply_markup=keyboard)

    async def show_news(self, callback: CallbackQuery):
        _, ticker, index_str = callback.data.split("_")
        index = int(index_str)

        news_list = await self.stock_service.get_news(ticker)

        if not news_list:
            await callback.answer("Новости для этой компании отсутствуют.", show_alert=True)
            return

        if index < 0 or index >= len(news_list):
            await callback.answer("Больше новостей нет.", show_alert=True)
            return
        
        MAX_LENGTH = 100  # порог длины

        news = news_list[index]
        sentiment = self._format_sentiment(news.positive, news.negative, news.neutral)
        formatted_date = news.date.strftime("%Y-%m-%d %H:%M")
        content = news.content
        if len(content) > MAX_LENGTH:
            content = content[:MAX_LENGTH] + "...\n\n📎 <a href='https://rasdevai.vercel.app'>Подробнее на сайте rasdevai.vercel.app</a>"

        text = (
            f"📰 <b>{news.title}</b>\n\n"
            f"{content}\n\n"
            f"📌 Источник: <i>{news.source}</i>\n"
            f"🗓 Дата: {formatted_date}\n"
            f"🧠 Анализ новости: {sentiment}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"news_{ticker}_{index - 1}" if index > 0 else f"news_{ticker}_0"
                ),
                InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"news_{ticker}_{index + 1}" if index < len(news_list) - 1 else f"news_{ticker}_{index}"
                )
            ],
            [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu_main")]
        ])

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

    # Вставь это в конец BotHandler
    async def show_main_menu(self, callback: CallbackQuery):
        await callback.message.answer("Главное меню:", reply_markup=self.main_menu())
        await callback.message.delete()  # удалим старое сообщение с кнопками

    async def show_forecast(self, callback: CallbackQuery):
        ticker = callback.data.split("_")[1]
        forecast = await self.stock_service.get_forecast(ticker)  # вернёт LSTMForecastResponseMonth

        if not forecast or not forecast.predicted_prices:
            await callback.answer("Прогноз недоступен.", show_alert=True)
            return

        forecast_text = "\n".join([
            f"📈 День {i + 1}: {price:.2f} USD"
            for i, price in enumerate(forecast.predicted_prices)
        ])

        await callback.message.answer(
            f"📉 Прогноз по <b>{ticker}</b> на неделю:\n\n{forecast_text}",
            reply_markup=self.back_to_main_menu(),
            parse_mode="HTML"
        )
        await callback.message.delete()

    async def show_price_history(self, callback: CallbackQuery):
        ticker = callback.data.split("_")[1]
        history: StockResponse = await self.stock_service.get_price_history(ticker)

        if not history or not history.priceData:
            await callback.answer("История цен недоступна.", show_alert=True)
            return

        price_lines = "\n".join([
            f"📅 {data.date}: {data.value:.2f} USD"
            for data in history.priceData[-7:]  # показываем последние 7 записей
        ])

        text = (
            f"🏢 <b>{history.companyName}</b> ({history.ticker})\n"
            f"💲 Текущая цена: {history.currentPrice:.2f} USD\n"
            f"📉 Изменение: {history.shareChange:.2f}%\n\n"
            f"💹 История цен за последнюю неделю:\n\n{price_lines}"
        )

        await callback.message.answer(
            text,
            reply_markup=self.back_to_main_menu(),
            parse_mode="HTML"
        )
        await callback.message.delete()


    def back_to_main_menu(self):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu_main")]
        ])


    def _format_sentiment(self, positive: float, negative: float, neutral: float) -> str:
        # Определим доминирующее значение
        if positive > negative and positive > neutral:
            return f"🟢 Позитивная ({positive:.2f})"
        elif negative > positive and negative > neutral:
            return f"🔴 Негативная ({negative:.2f})"
        else:
            return f"⚪ Нейтральная ({neutral:.2f})"


# В точке запуска бота:
# from bot.handlers import BotHandler
# bot_handler = BotHandler()
# dp.include_router(bot_handler.router)
