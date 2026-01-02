# simplest_bot.py
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 1. Получаем токен
try:
    from config import BOT_TOKEN
    print(f"✅ Токен: {BOT_TOKEN[:10]}...")
except:
    print("❌ Нет токена")
    sys.exit(1)

# 2. Импортируем aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 3. Создаем бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    """Самая простая команда"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Бургер", callback_data="burger")],
        [InlineKeyboardButton(text="🍕 Пицца", callback_data="pizza")]
    ])
    
    await message.answer(
        f"Привет, {message.from_user.first_name}!\n"
        f"Выбери еду:",
        reply_markup=keyboard
    )
    print(f"✅ {message.from_user.id} запустил бота")

@dp.callback_query()
async def button(call: types.CallbackQuery):
    """Обработка кнопок"""
    if call.data == "burger":
        await call.answer("🍔 Выбрал бургер!")
        await call.message.edit_text("Вы выбрали 🍔 бургер!\nЦена: 299₽")
    elif call.data == "pizza":
        await call.answer("🍕 Выбрал пиццу!")
        await call.message.edit_text("Вы выбрали 🍕 пиццу!\nЦена: 499₽")

@dp.message()
async def echo(message: types.Message):
    await message.answer("Напишите /start")

async def main():
    print("🚀 Самый простой бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
