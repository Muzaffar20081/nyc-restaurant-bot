# super_simple_bot.py - САМЫЙ ПРОСТОЙ РАБОЧИЙ БОТ
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 1. Получаем токен
try:
    from config import BOT_TOKEN
    print(f"✅ Токен: {BOT_TOKEN[:10]}...")
except:
    print("❌ Нет токена в config.py")
    sys.exit(1)

# 2. Импортируем aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# 3. Создаем бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 4. Простейшее меню
MENU = {
    "burgers": "🍔 Бургеры",
    "pizza": "🍕 Пицца", 
    "sushi": "🍣 Суши"
}

# 5. Корзина (просто список)
cart = {}

@dp.message(CommandStart())
async def start(message: types.Message):
    """Самая простая команда /start"""
    
    # Создаем кнопки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Бургеры", callback_data="burgers")],
        [InlineKeyboardButton(text="🍕 Пицца", callback_data="pizza")],
        [InlineKeyboardButton(text="🍣 Суши", callback_data="sushi")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
    ])
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Выберите категорию:",
        reply_markup=keyboard
    )
    print(f"✅ Пользователь {message.from_user.id} запустил бота")

@dp.callback_query()
async def handle_button(call: types.CallbackQuery):
    """Обработка ВСЕХ кнопок"""
    button = call.data
    
    if button in ["burgers", "pizza", "sushi"]:
        await call.answer(f"Выбрана категория: {MENU[button]}")
        await call.message.edit_text(
            f"Вы выбрали: {MENU[button]}\n\n"
            f"Эта функция пока в разработке 😊\n"
            f"Используйте команду /start для возврата",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
            ])
        )
    
    elif button == "cart":
        await call.answer("Корзина")
        await call.message.edit_text(
            "🛒 Корзина\n\n"
            "Эта функция пока в разработке 😊\n"
            f"Используйте команду /start для возврата",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
            ])
        )
    
    elif button == "back":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍔 Бургеры", callback_data="burgers")],
            [InlineKeyboardButton(text="🍕 Пицца", callback_data="pizza")],
            [InlineKeyboardButton(text="🍣 Суши", callback_data="sushi")],
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
        ])
        
        await call.message.edit_text(
            f"👋 Выберите категорию:",
            reply_markup=keyboard
        )
        await call.answer("Вернулись в меню")

@dp.message()
async def echo(message: types.Message):
    """Ответ на любое сообщение"""
    await message.answer(
        "Напишите /start чтобы начать\n\n"
        "Или выберите команду:\n"
        "• /start - начать\n"
        "• /help - помощь"
    )

async def main():
    """Главная функция"""
    print("🚀 Запускаю САМЫЙ ПРОСТОЙ бота...")
    print("📱 Откройте Telegram и найдите своего бота")
    print("💬 Отправьте /start")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Проверяем aiogram
    try:
        import aiogram
        print(f"✅ aiogram установлен, версия: {aiogram.__version__}")
    except ImportError:
        print("❌ aiogram не установлен!")
        print("Установите: pip install aiogram")
        sys.exit(1)
    
    asyncio.run(main())
