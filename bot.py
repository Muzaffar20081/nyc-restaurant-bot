# debug_bot.py
import asyncio
import os
import sys
import logging

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.DEBUG)

# 1. Проверяем config
try:
    from config import BOT_TOKEN, CUISINES
    print(f"✅ config.py загружен")
    print(f"   Токен: {BOT_TOKEN[:15]}...")
    print(f"   Кухни: {CUISINES}")
except Exception as e:
    print(f"❌ Ошибка config.py: {e}")
    sys.exit(1)

# 2. Проверяем меню
try:
    from menu import get_menu_by_category
    print(f"✅ menu загружен")
    
    # Тестируем каждую кухню
    for cuisine_id in CUISINES.keys():
        items = get_menu_by_category(cuisine_id)
        print(f"   {cuisine_id}: {len(items)} товаров")
        for item in items[:2]:  # Показываем первые 2 товара
            print(f"     - {item['name']}: {item['price']}₽")
except Exception as e:
    print(f"❌ Ошибка menu: {e}")
    import traceback
    traceback.print_exc()

# 3. Простейший бот
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    """Простой старт"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Бургеры", callback_data="burgers")],
        [InlineKeyboardButton(text="🍕 Пицца", callback_data="pizza")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
    ])
    
    await message.answer(
        f"👋 Привет! Это тест бота.\nНажми кнопку:",
        reply_markup=keyboard
    )

@dp.callback_query()
async def handle_callback(call: types.CallbackQuery):
    await call.answer(f"Нажата кнопка: {call.data}")

@dp.message()
async def echo(message: types.Message):
    await message.answer(f"Вы написали: {message.text}")

async def main():
    print("\n🚀 Запускаю тестовый бот...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
