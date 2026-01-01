# test_bot_working.py
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 1. Простое меню
SIMPLE_MENU = {
    "burgers": [
        {"id": "1", "name": "Чизбургер", "price": 199, "description": "Вкусный", "category": "burgers"},
    ],
    "pizza": [
        {"id": "2", "name": "Маргарита", "price": 399, "description": "С сыром", "category": "pizza"},
    ]
}

# 2. Получаем токен из config.py
try:
    from config import BOT_TOKEN
    print(f"✅ Токен: {BOT_TOKEN[:10]}...")
except:
    print("❌ Нет config.py с BOT_TOKEN")
    sys.exit(1)

# 3. Импортируем aiogram
try:
    from aiogram import Bot, Dispatcher, types
    from aiogram.filters import CommandStart
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    print("✅ aiogram загружен")
except ImportError:
    print("❌ Установите aiogram: pip install aiogram")
    sys.exit(1)

# 4. Создаем бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
cart = {}

@dp.message(CommandStart())
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Бургеры", callback_data="burgers")],
        [InlineKeyboardButton(text="🍕 Пицца", callback_data="pizza")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
    ])
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"Это тестовый бот.\n"
        f"Нажмите кнопку:",
        reply_markup=keyboard
    )
    print(f"✅ Пользователь {message.from_user.id} запустил бота")

@dp.callback_query()
async def handle_all(call: types.CallbackQuery):
    data = call.data
    
    if data in ["burgers", "pizza"]:
        items = SIMPLE_MENU.get(data, [])
        
        if not items:
            await call.answer("Нет товаров")
            return
        
        # Показываем товары
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
            f"{'🍔 Бургеры' if data == 'burgers' else '🍕 Пицца'}\n\nВыберите:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    
    elif data.startswith("item_"):
        item_id = data[5:]
        
        # Ищем товар
        for cat_items in SIMPLE_MENU.values():
            for item in cat_items:
                if item["id"] == item_id:
                    text = f"*{item['name']}*\n\n{item['description']}\n\n💰 {item['price']}₽"
                    
                    await call.message.edit_text(
                        text,
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="➕ Добавить", callback_data=f"add_{item_id}")],
                            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
                        ]),
                        parse_mode="Markdown"
                    )
                    await call.answer()
                    return
        
        await call.answer("Не найден")
    
    elif data.startswith("add_"):
        item_id = data[4:]
        user_id = call.from_user.id
        
        # Ищем и добавляем
        for cat_items in SIMPLE_MENU.values():
            for item in cat_items:
                if item["id"] == item_id:
                    if user_id not in cart:
                        cart[user_id] = []
                    cart[user_id].append(item)
                    
                    await call.answer(f"✅ {item['name']} добавлен!")
                    
                    # Возвращаем
                    call.data = item['category']
                    await handle_all(call)
                    return
        
        await call.answer("Ошибка")
    
    elif data == "cart":
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
        await call.answer()
    
    elif data == "back":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍔 Бургеры", callback_data="burgers")],
            [InlineKeyboardButton(text="🍕 Пицца", callback_data="pizza")],
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
        ])
        await call.message.edit_text("Выберите категорию:", reply_markup=keyboard)
        await call.answer()
    
    else:
        await call.answer(f"Кнопка: {data}")

@dp.message()
async def echo(message: types.Message):
    await message.answer("Напишите /start")

async def main():
    print("🚀 Запускаю тестовый бот...")
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
