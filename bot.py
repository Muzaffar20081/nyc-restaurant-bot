# simple_bot.py - МИНИМАЛЬНЫЙ РАБОЧИЙ БОТ
import asyncio
import os
import sys
import logging

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# Импортируем config
try:
    from config import BOT_TOKEN, CUISINES
    print(f"✅ Токен загружен: {BOT_TOKEN[:10]}...")
except ImportError:
    print("❌ Ошибка: файл config.py не найден или не содержит BOT_TOKEN")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Простое меню для теста
TEST_MENU = {
    "burgers": [
        {"id": "whopper", "name": "Воппер", "price": 299, "description": "Классический бургер", "category": "burgers"},
        {"id": "cheeseburger", "name": "Чизбургер", "price": 199, "description": "С сыром", "category": "burgers"},
    ],
    "italy": [
        {"id": "margarita", "name": "Маргарита", "price": 499, "description": "Пицца", "category": "italy"},
        {"id": "pasta", "name": "Паста", "price": 399, "description": "Спагетти", "category": "italy"},
    ],
    "sushi": [
        {"id": "philadelphia", "name": "Филадельфия", "price": 399, "description": "Ролл", "category": "sushi"},
        {"id": "california", "name": "Калифорния", "price": 359, "description": "Ролл с крабом", "category": "sushi"},
    ]
}

# Корзина
user_cart = {}

def create_main_keyboard():
    """Создает главную клавиатуру"""
    buttons = []
    
    # Создаем кнопки из CUISINES
    items = list(CUISINES.items())
    
    # Размещаем по 2 в ряд
    for i in range(0, len(items), 2):
        row = []
        if i < len(items):
            cat_id, cat_name = items[i]
            row.append(InlineKeyboardButton(text=cat_name, callback_data=f"cat_{cat_id}"))
        if i + 1 < len(items):
            cat_id, cat_name = items[i + 1]
            row.append(InlineKeyboardButton(text=cat_name, callback_data=f"cat_{cat_id}"))
        if row:
            buttons.append(row)
    
    # Кнопка корзины
    buttons.append([InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(CommandStart())
async def start(message: types.Message):
    """Обработчик /start"""
    user_id = message.from_user.id
    user_cart[user_id] = []  # Инициализируем корзину
    
    keyboard = create_main_keyboard()
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"*MYC RESTAURANT*\n\n"
        f"Выберите кухню:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data.startswith("cat_"))
async def show_category(call: types.CallbackQuery):
    """Показать категорию"""
    cat_id = call.data[4:]  # cat_burgers -> burgers
    
    if cat_id not in TEST_MENU:
        await call.answer("Категория не найдена")
        return
    
    items = TEST_MENU[cat_id]
    cat_name = CUISINES.get(cat_id, "Категория")
    
    # Создаем кнопки товаров
    buttons = []
    for item in items:
        buttons.append([
            InlineKeyboardButton(
                text=f"{item['name']} - {item['price']}₽",
                callback_data=f"item_{item['id']}"
            )
        ])
    
    # Кнопки навигации
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="back"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")
    ])
    
    await call.message.edit_text(
        f"*{cat_name}*\n\nВыберите блюдо:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("item_"))
async def show_item(call: types.CallbackQuery):
    """Показать товар"""
    item_id = call.data[5:]  # item_whopper -> whopper
    
    # Ищем товар во всех категориях
    item = None
    for cat_items in TEST_MENU.values():
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
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"cat_{item['category']}"),
            InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")
        ]
    ])
    
    await call.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(call: types.CallbackQuery):
    """Добавить в корзину"""
    item_id = call.data[4:]
    user_id = call.from_user.id
    
    # Ищем товар
    item = None
    for cat_items in TEST_MENU.values():
        for it in cat_items:
            if it["id"] == item_id:
                item = it
                break
        if item:
            break
    
    if not item:
        await call.answer("Товар не найден")
        return
    
    # Инициализируем корзину если нужно
    if user_id not in user_cart:
        user_cart[user_id] = []
    
    # Добавляем в корзину
    user_cart[user_id].append(item)
    
    await call.answer(f"✅ {item['name']} добавлен в корзину!", show_alert=True)
    
    # Возвращаемся к категории
    call.data = f"cat_{item['category']}"
    await show_category(call)

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    """Показать корзину"""
    user_id = call.from_user.id
    
    if user_id not in user_cart or not user_cart[user_id]:
        text = "*🛒 Корзина пуста*\n\nДобавьте товары из меню!"
        keyboard = [[InlineKeyboardButton(text="📋 К меню", callback_data="back")]]
    else:
        items = user_cart[user_id]
        total = sum(item["price"] for item in items)
        
        # Считаем количество каждого товара
        counts = {}
        for item in items:
            name = item['name']
            counts[name] = counts.get(name, 0) + 1
        
        text = "*🛒 Ваша корзина:*\n\n"
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
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(call: types.CallbackQuery):
    """Очистить корзину"""
    user_id = call.from_user.id
    if user_id in user_cart:
        user_cart[user_id].clear()
        await call.answer("Корзина очищена!", show_alert=True)
    
    await show_cart(call)

@dp.callback_query(lambda c: c.data == "checkout")
async def checkout(call: types.CallbackQuery):
    """Оформить заказ"""
    user_id = call.from_user.id
    
    if user_id not in user_cart or not user_cart[user_id]:
        await call.answer("Корзина пуста!", show_alert=True)
        return
    
    items = user_cart[user_id]
    total = sum(item["price"] for item in items)
    count = len(items)
    
    # Очищаем корзину
    user_cart[user_id].clear()
    
    await call.message.edit_text(
        f"✅ *Заказ принят!*\n\n"
        f"Позиций: {count}\n"
        f"Сумма: {total}₽\n\n"
        f"Спасибо за заказ! 🎉",
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "back")
async def back_to_menu(call: types.CallbackQuery):
    """Вернуться в меню"""
    keyboard = create_main_keyboard()
    
    await call.message.edit_text(
        "*MYC RESTAURANT*\n\nВыберите кухню:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await call.answer()

@dp.message()
async def handle_text(message: types.Message):
    """Обработчик текстовых сообщений"""
    text = message.text.strip().lower()
    
    if text in ["меню", "menu", "start"]:
        keyboard = create_main_keyboard()
        await message.answer(
            "*MYC RESTAURANT*\n\nВыберите кухню:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return
    
    if text in ["корзина", "cart"]:
        user_id = message.from_user.id
        
        if user_id not in user_cart or not user_cart[user_id]:
            await message.answer("*🛒 Корзина пуста!*", parse_mode="Markdown")
            return
        
        items = user_cart[user_id]
        total = sum(item["price"] for item in items)
        
        counts = {}
        for item in items:
            name = item['name']
            counts[name] = counts.get(name, 0) + 1
        
        text_response = "*🛒 Ваша корзина:*\n\n"
        for name, count in counts.items():
            price = next(i["price"] for i in items if i["name"] == name)
            text_response += f"• {name} ×{count} = {price * count}₽\n"
        
        text_response += f"\n💰 *Итого: {total}₽*"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ Очистить", callback_data="clear_cart")],
            [InlineKeyboardButton(text="✅ Оформить", callback_data="checkout")],
            [InlineKeyboardButton(text="📋 К меню", callback_data="back")]
        ])
        
        await message.answer(text_response, reply_markup=keyboard, parse_mode="Markdown")
        return
    
    await message.answer("Используйте кнопки меню или напишите 'меню'")

async def main():
    """Главная функция"""
    logger.info("🚀 Запуск MYC RESTAURANT бота...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
