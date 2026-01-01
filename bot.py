# working_bot.py
import asyncio
import os
import sys
import logging
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# Получаем конфиг
try:
    from config import BOT_TOKEN, CUISINES
    print(f"✅ config.py загружен")
except ImportError as e:
    print(f"❌ Ошибка config.py: {e}")
    sys.exit(1)

# Получаем реальное меню
try:
    from menu import get_menu_by_category, find_item_by_id, search_items
    print(f"✅ Меню загружено")
except ImportError as e:
    print(f"❌ Ошибка меню: {e}")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Корзина
user_cart = defaultdict(list)

def create_menu():
    """Создает главное меню"""
    buttons = []
    
    # Кнопки категорий
    for cat_id, cat_name in CUISINES.items():
        buttons.append([InlineKeyboardButton(text=cat_name, callback_data=f"cat_{cat_id}")])
    
    # Кнопка корзины
    buttons.append([InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(CommandStart())
async def start(message: types.Message):
    """Команда /start"""
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} запустил бота")
    
    menu = create_menu()
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"*MYC RESTAURANT*\n\n"
        f"Выберите кухню:",
        reply_markup=menu,
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data.startswith("cat_"))
async def show_category(call: types.CallbackQuery):
    """Показать категорию"""
    cat_id = call.data[4:]  # cat_burgers -> burgers
    
    items = get_menu_by_category(cat_id)
    
    if not items:
        await call.answer("Нет товаров")
        return
    
    cat_name = CUISINES.get(cat_id, "Категория")
    
    # Кнопки товаров
    buttons = []
    for item in items:
        emoji = item.get('image', '🍽️')
        buttons.append([
            InlineKeyboardButton(
                text=f"{emoji} {item['name']} - {item['price']}₽",
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
    
    item = find_item_by_id(item_id)
    
    if not item:
        await call.answer("Не найден")
        return
    
    # Описание товара
    description = f"*{item['name']}*\n\n{item.get('description', '')}\n"
    
    if 'weight' in item:
        description += f"Вес: {item['weight']}\n"
    if 'size' in item:
        description += f"Размер: {item['size']}\n"
    
    description += f"\nЦена: *{item['price']}₽*"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"➕ Добавить ({item['price']}₽)", callback_data=f"add_{item_id}")],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"cat_{item['category']}"),
            InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")
        ]
    ])
    
    await call.message.edit_text(
        description,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(call: types.CallbackQuery):
    """Добавить в корзину"""
    item_id = call.data[4:]
    user_id = call.from_user.id
    
    item = find_item_by_id(item_id)
    
    if not item:
        await call.answer("Не найден")
        return
    
    user_cart[user_id].append(item)
    
    await call.answer(f"✅ {item['name']} добавлен!", show_alert=True)
    
    # Возвращаемся
    call.data = f"cat_{item['category']}"
    await show_category(call)

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    """Показать корзину"""
    user_id = call.from_user.id
    items = user_cart[user_id]
    
    if not items:
        text = "*🛒 Корзина пуста*\n\nДобавьте товары!"
        keyboard = [[InlineKeyboardButton(text="📋 Меню", callback_data="back")]]
    else:
        total = sum(item["price"] for item in items)
        
        # Считаем товары
        counts = {}
        for item in items:
            name = item['name']
            counts[name] = counts.get(name, 0) + 1
        
        text = "*🛒 Корзина:*\n\n"
        for name, count in counts.items():
            price = next(i["price"] for i in items if i["name"] == name)
            text += f"• {name} ×{count} = {price * count}₽\n"
        
        text += f"\n*Итого: {total}₽*"
        
        keyboard = [
            [InlineKeyboardButton(text="🗑️ Очистить", callback_data="clear_cart")],
            [InlineKeyboardButton(text="✅ Оформить", callback_data="checkout")],
            [InlineKeyboardButton(text="📋 Меню", callback_data="back")]
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
        await call.answer("Очищено!", show_alert=True)
    
    await show_cart(call)

@dp.callback_query(lambda c: c.data == "checkout")
async def checkout(call: types.CallbackQuery):
    """Оформить заказ"""
    user_id = call.from_user.id
    items = user_cart.get(user_id, [])
    
    if not items:
        await call.answer("Корзина пуста!", show_alert=True)
        return
    
    total = sum(item["price"] for item in items)
    count = len(items)
    
    # Очищаем
    user_cart[user_id].clear()
    
    await call.message.edit_text(
        f"✅ *Заказ принят!*\n\n"
        f"Позиций: {count}\n"
        f"Сумма: {total}₽\n\n"
        f"Спасибо! 🎉",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Новый заказ", callback_data="back")]
        ]),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "back")
async def back_to_menu(call: types.CallbackQuery):
    """Вернуться в меню"""
    menu = create_menu()
    
    await call.message.edit_text(
        "*MYC RESTAURANT*\n\nВыберите кухню:",
        reply_markup=menu,
        parse_mode="Markdown"
    )
    await call.answer()

@dp.message()
async def text_handler(message: types.Message):
    """Обработка текста"""
    text = message.text.strip().lower()
    
    if text in ["меню", "menu", "start"]:
        menu = create_menu()
        await message.answer(
            "*MYC RESTAURANT*\n\nВыберите кухню:",
            reply_markup=menu,
            parse_mode="Markdown"
        )
        return
    
    if text in ["корзина", "cart"]:
        user_id = message.from_user.id
        items = user_cart[user_id]
        
        if not items:
            await message.answer("*🛒 Корзина пуста!*", parse_mode="Markdown")
            return
        
        total = sum(item["price"] for item in items)
        
        counts = {}
        for item in items:
            name = item['name']
            counts[name] = counts.get(name, 0) + 1
        
        text_response = "*🛒 Корзина:*\n\n"
        for name, count in counts.items():
            price = next(i["price"] for i in items if i["name"] == name)
            text_response += f"• {name} ×{count} = {price * count}₽\n"
        
        text_response += f"\n*Итого: {total}₽*"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ Очистить", callback_data="clear_cart")],
            [InlineKeyboardButton(text="✅ Оформить", callback_data="checkout")],
            [InlineKeyboardButton(text="📋 Меню", callback_data="back")]
        ])
        
        await message.answer(text_response, reply_markup=keyboard, parse_mode="Markdown")
        return
    
    # Поиск
    if len(text) > 2:
        results = search_items(text)
        if results:
            response = "🔍 *Найдено:*\n\n"
            for item in results[:5]:
                response += f"• {item['name']} - {item['price']}₽\n"
            await message.answer(response, parse_mode="Markdown")
            return
    
    await message.answer("Напишите 'меню' или 'корзина'")

async def main():
    """Запуск"""
    logger.info("🚀 Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
