from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.services.login_service import LoginService

# Состояния логина
class LoginStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()

# Создаем router
router = Router()

def register_handlers(router: Router):
    
    @router.message(F.text.in_({"/start", "/login"}))
    async def start(message: Message, state: FSMContext):
        await message.answer("Введите email:")
        await state.set_state(LoginStates.waiting_for_email)

    @router.message(LoginStates.waiting_for_email)
    async def email_entered(message: Message, state: FSMContext):
        await state.update_data(email=message.text)
        await message.answer("Введите пароль:")
        await state.set_state(LoginStates.waiting_for_password)

    @router.message(LoginStates.waiting_for_password)
    async def password_entered(message: Message, state: FSMContext):
        data = await state.get_data()
        email = data.get("email")
        password = message.text

        login_service = LoginService()
        try:
            telegram_id = message.from_user.id
            is_success = await login_service.login_user(email, password, telegram_id)
            if is_success:
                await message.answer("Успешный вход. Telegram ID привязан.")
            else:
                await message.answer("Неверные данные или email не подтверждён.")
        except Exception as e:
            await message.answer("Произошла неизвестная ошибка")
            await state.clear()
            print(e)
