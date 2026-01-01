# minimal_bot.py
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# Простое меню
MENU = {
    "burgers": [
        {"id": "1", "name": "Чизбургер", "price": 199, "description": "Вкусный бургер"},
        {"id": "2", "name": "Гамбургер", "price": 179, "description": "Классика"},
    ],
    "pizza": [
        {"id": "3", "name": "Маргарита", "price": 399, "description": "С моцареллой"},
        {"id": "4", "name": "Пепперони", "price": 449, "description": "Острая"},
    ]
}

# Токен из config.py
try:
    from config import BOT_TOKEN
    TOKEN = BOT_TOKEN
except:
    print("❌ Нет токена в config.py")
    sys.exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher()
cart = {}

@dp.message(CommandStart())
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Бургеры", callback_data="burgers")],
        [InlineKeyboardButton(text="🍕 Пицца", callback_data="pizza")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
    ])
    
    await message.answer("Выберите категорию:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data in ["burgers", "pizza"])
async def category(call: types.CallbackQuery):
    cat = call.data
    items = MENU.get(cat, [])
    
    buttons = []
    for item in items:
        buttons.append([
            InlineKeyboardButton(
                text=f"{item['name']} - {item['price']}₽",
                callback_data=f"item_{item['id']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back")])
    
    await call.message.edit_text(
        f"{'🍔 Бургеры' if cat == 'burgers' else '🍕 Пицца'}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.callback_query(lambda c: c.data.startswith("item_"))
async def item(call: types.CallbackQuery):
    item_id = call.data[5:]
    
    # Ищем товар
    for cat_items in MENU.values():
        for item in cat_items:
            if item["id"] == item_id:
                text = f"*{item['name']}*\n\n{item['description']}\n\n💰 {item['price']}₽"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=f"➕ Добавить", callback_data=f"add_{item_id}")],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
                ])
                
                await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
                return
    
    await call.answer("Товар не найден")

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    items = cart.get(user_id, [])
    
    if not items:
        text = "🛒 Корзина пуста"
    else:
        total = sum(i["price"] for i in items)
        text = f"🛒 Корзина:\n\n"
        for item in items:
            text += f"• {item['name']} - {item['price']}₽\n"
        text += f"\nИтого: {total}₽"
    
    await call.message.edit_text(text)

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add(call: types.CallbackQuery):
    item_id = call.data[4:]
    user_id = call.from_user.id
    
    # Ищем товар
    for cat_items in MENU.values():
        for item in cat_items:
            if item["id"] == item_id:
                if user_id not in cart:
                    cart[user_id] = []
                cart[user_id].append(item)
                await call.answer(f"✅ {item['name']} добавлен!")
                await category(call)  # Возвращаемся
                return
    
    await call.answer("Ошибка")

@dp.callback_query(lambda c: c.data == "back")
async def back(call: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Бургеры", callback_data="burgers")],
        [InlineKeyboardButton(text="🍕 Пицца", callback_data="pizza")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
    ])
    await call.message.edit_text("Выберите категорию:", reply_markup=keyboard)

@dp.message()
async def echo(message: types.Message):
    await message.answer("Напишите /start")

async def main():
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
