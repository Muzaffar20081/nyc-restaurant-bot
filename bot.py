# bot.py — версия для локального тестирования (polling)
import asyncio
import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import config
from menus import MENU_BY_CUISINE
from ai_brain import ask_ai

router = Router()

class OrderStates(StatesGroup):
    CHOOSE_CUISINE = State()
    VIEW_MENU = State()

def get_cuisine_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=data["name"], callback_data=f"cuisine:{key}")]
        for key, data in MENU_BY_CUISINE.items()
    ])

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать в NYC Restaurant Bot! 🍔🍕🍣\n\nВыберите кухню:",
        reply_markup=get_cuisine_kb()
    )
    await state.set_state(OrderStates.CHOOSE_CUISINE)

@router.callback_query(F.data.startswith("cuisine:"))
async def select_cuisine(call: CallbackQuery, state: FSMContext):
    _, cuisine = call.data.split(":", 1)
    if cuisine not in MENU_BY_CUISINE:
        await call.message.answer("Ошибка выбора. Попробуйте /start")
        await call.answer()
        return

    data = MENU_BY_CUISINE[cuisine]
    await state.update_data(cuisine=cuisine)

    ai_response = ask_ai(f"Клиент выбрал {data['name']}")

    await call.message.edit_text(
        f"{data['text']}\n\n{ai_response}\n\n(пока меню в разработке)",
        parse_mode="HTML"
    )
    await call.answer()

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
