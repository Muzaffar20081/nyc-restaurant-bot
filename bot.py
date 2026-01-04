# ultra_simple_bot.py
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Получаем токен
try:
    from config import BOT_TOKEN
    print(f"✅ Токен: {BOT_TOKEN[:10]}...")
except:
    print("❌ Нет config.py")
    sys.exit(1)

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    """Самая простая команда"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Бургер", callback_data="burger")],
        [InlineKeyboardButton(text="🍕 Пицца", callback_data="pizza")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
    ])
    
    await message.answer(
        f"Привет, {message.from_user.first_name}!\n"
        f"Выбери еду:",
        reply_markup=keyboard
    )
    print(f"✅ {message.from_user.id} запустил бота")

@dp.callback_query()
async def handle_button(call: types.CallbackQuery):
    data = call.data
    
    if data == "burger":
        await call.answer("🍔 Бургер!")
        await call.message.edit_text(
            "Вы выбрали 🍔 бургер!\n\n"
            "Цена: 299₽\n\n"
            "Хотите добавить в корзину?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить", callback_data="add_burger")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
            ])
        )
    
    elif data == "pizza":
        await call.answer("🍕 Пицца!")
        await call.message.edit_text(
            "Вы выбрали 🍕 пиццу!\n\n"
            "Цена: 499₽\n\n"
            "Хотите добавить в корзину?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить", callback_data="add_pizza")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
            ])
        )
    
    elif data == "add_burger":
        await call.answer("✅ Бургер добавлен!")
        # Используем новую функцию show_main_menu
        await show_main_menu(call.message)
    
    elif data == "add_pizza":
        await call.answer("✅ Пицца добавлена!")
        # Используем новую функцию show_main_menu
        await show_main_menu(call.message)
    
    elif data == "cart":
        await call.answer("🛒 Корзина")
        await call.message.edit_text(
            "🛒 Корзина:\n\n"
            "• Бургер - 299₽\n"
            "• Пицца - 499₽\n\n"
            "Итого: 798₽",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Оформить", callback_data="order")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
            ])
        )
    
    elif data == "order":
        await call.answer("✅ Заказ оформлен!")
        await call.message.edit_text(
            "✅ Заказ принят!\n\n"
            "Спасибо за заказ! 🎉\n"
            "Ожидайте звонка оператора."
        )
    
    elif data == "back":
        # Используем новую функцию show_main_menu
        await show_main_menu(call.message)
        await call.answer("Назад")

async def show_main_menu(message_or_call):
    """Функция для показа главного меню"""
    if isinstance(message_or_call, types.CallbackQuery):
        message = message_or_call.message
    else:
        message = message_or_call
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Бургер", callback_data="burger")],
        [InlineKeyboardButton(text="🍕 Пицца", callback_data="pizza")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
    ])
    
    await message.edit_text(
        "Выбери еду:",
        reply_markup=keyboard
    )

@dp.message()
async def echo(message: types.Message):
    await message.answer("Напишите /start")

async def main():
    print("🚀 Ультра-простой бот запускается...")
    print("📱 Откройте Telegram, найдите бота")
    print("💬 Напишите /start")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
