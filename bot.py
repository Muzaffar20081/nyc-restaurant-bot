# simple_bot.py — МИНИМАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ
import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# Включаем логирование для отладки
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Создаем простые данные для теста
SIMPLE_MENU = {
    "burgers": [
        {"id": "whopper", "name": "Воппер", "price": 299, "description": "Классический бургер", "category": "burgers"},
        {"id": "cheeseburger", "name": "Чизбургер", "price": 199, "description": "С сыром", "category": "burgers"},
    ],
    "pizza": [
        {"id": "margarita", "name": "Маргарита", "price": 499, "description": "Классическая пицца", "category": "pizza"},
        {"id": "pepperoni", "name": "Пепперони", "price": 549, "description": "Острая пицца", "category": "pizza"},
    ]
}

CATEGORIES = [
    {"id": "burgers", "name": "🍔 Бургеры"},
    {"id": "pizza", "name": "🍕 Пицца"},
]

# Инициализация бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ ОШИБКА: Токен не найден!")
    print("Создайте файл .env с BOT_TOKEN=ваш_токен")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Простая корзина
cart = {}

@dp.message(CommandStart())
async def start(message: types.Message):
    """Простой старт"""
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    
    # Создаем кнопки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Бургеры", callback_data="cat_burgers")],
        [InlineKeyboardButton(text="🍕 Пицца", callback_data="cat_pizza")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
    ])
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Это тестовый бот. Выбери категорию:",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

@dp.callback_query(lambda c: c.data.startswith("cat_"))
async def show_category(call: types.CallbackQuery):
    """Показать категорию"""
    cat_id = call.data[4:]  # Убираем "cat_"
    items = SIMPLE_MENU.get(cat_id, [])
    
    if not items:
        await call.answer("Категория пуста")
        return
    
    # Создаем кнопки товаров
    keyboard = []
    for item in items:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{item['name']} - {item['price']}₽",
                callback_data=f"item_{item['id']}"
            )
        ])
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back")])
    
    cat_name = "🍔 Бургеры" if cat_id == "burgers" else "🍕 Пицца"
    
    await call.message.edit_text(
        f"*{cat_name}*\n\nВыбери блюдо:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("item_"))
async def show_item(call: types.CallbackQuery):
    """Показать товар"""
    item_id = call.data[5:]  # Убираем "item_"
    
    # Ищем товар
    item = None
    for cat_items in SIMPLE_MENU.values():
        for it in cat_items:
            if it["id"] == item_id:
                item = it
                break
        if item:
            break
    
    if not item:
        await call.answer("Товар не найден")
        return
    
    text = f"*{item['name']}*\n\n{item['description']}\n\n💰 *Цена: {item['price']}₽*"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"➕ Добавить ({item['price']}₽)", callback_data=f"add_{item_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"cat_{item['category']}")]
    ])
    
    await call.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(call: types.CallbackQuery):
    """Добавить в корзину"""
    item_id = call.data[4:]  # Убираем "add_"
    
    # Ищем товар
    item = None
    for cat_items in SIMPLE_MENU.values():
        for it in cat_items:
            if it["id"] == item_id:
                item = it
                break
        if item:
            break
    
    if not item:
        await call.answer("Товар не найден")
        return
    
    user_id = call.from_user.id
    if user_id not in cart:
        cart[user_id] = []
    
    cart[user_id].append(item)
    await call.answer(f"✅ {item['name']} добавлен в корзину!", show_alert=True)
    
    # Возвращаемся к категории
    await show_category(call)

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    """Показать корзину"""
    user_id = call.from_user.id
    items = cart.get(user_id, [])
    
    if not items:
        text = "*🛒 Корзина пуста!*\n\nДобавь товары из меню."
        keyboard = [[InlineKeyboardButton(text="📋 К меню", callback_data="back")]]
    else:
        total = sum(item["price"] for item in items)
        counts = {}
        for item in items:
            counts[item["name"]] = counts.get(item["name"], 0) + 1
        
        text = "*🛒 Твоя корзина:*\n\n"
        for name, count in counts.items():
            price = next(i["price"] for i in items if i["name"] == name)
            text += f"• {name} ×{count} = {price * count}₽\n"
        
        text += f"\n💰 *Итого: {total}₽*"
        
        keyboard = [
            [InlineKeyboardButton(text="🗑️ Очистить", callback_data="clear_cart")],
            [InlineKeyboardButton(text="✅ Оформить", callback_data="checkout")],
            [InlineKeyboardButton(text="📋 К меню", callback_data="back")]
        ]
    
    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(call: types.CallbackQuery):
    """Очистить корзину"""
    user_id = call.from_user.id
    if user_id in cart:
        cart[user_id].clear()
        await call.answer("Корзина очищена!", show_alert=True)
    await show_cart(call)

@dp.callback_query(lambda c: c.data == "checkout")
async def checkout(call: types.CallbackQuery):
    """Оформить заказ"""
    user_id = call.from_user.id
    items = cart.get(user_id, [])
    
    if not items:
        await call.answer("Корзина пуста!", show_alert=True)
        return
    
    total = sum(item["price"] for item in items)
    
    cart[user_id].clear()
    
    await call.message.edit_text(
        f"✅ *Заказ оформлен!*\n\nСумма: {total}₽\n\nСпасибо за заказ! 🎉",
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "back")
async def back_to_menu(call: types.CallbackQuery):
    """Вернуться в меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Бургеры", callback_data="cat_burgers")],
        [InlineKeyboardButton(text="🍕 Пицца", callback_data="cat_pizza")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
    ])
    
    await call.message.edit_text(
        "👋 Выбери категорию:",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@dp.message()
async def handle_text(message: types.Message):
    """Обработка текста"""
    await message.answer("Используй кнопки меню или напиши /start")

async def main():
    logger.info("🚀 Запускаю простого бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
