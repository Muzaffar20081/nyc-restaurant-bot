# bot.py — ФИНАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ
import asyncio
import os
import sys
import logging
from collections import defaultdict

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# Импортируем config
try:
    from config import BOT_TOKEN, CUISINES
    print(f"✅ Конфиг загружен")
except ImportError as e:
    print(f"❌ Ошибка загрузки config.py: {e}")
    sys.exit(1)

# Пробуем импортировать меню
try:
    from menu import get_menu_by_category, find_item_by_id, search_items
    print(f"✅ Меню загружено")
    USE_REAL_MENU = True
except ImportError:
    print("⚠️  Меню не загружено, используется тестовое меню")
    USE_REAL_MENU = False

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Корзина пользователей
user_cart = defaultdict(list)

# Тестовое меню (на случай если real menu не загрузится)


def get_items_by_category(category_id):
    """Получить товары категории"""
    if USE_REAL_MENU:
        return get_menu_by_category(category_id)
    else:
        return TEST_MENU.get(category_id, [])

def find_item(item_id):
    """Найти товар по ID"""
    if USE_REAL_MENU:
        return find_item_by_id(item_id)
    else:
        # Ищем в тестовом меню
        for cat_items in TEST_MENU.values():
            for item in cat_items:
                if item["id"] == item_id:
                    return item
        return None

def search_items_in_menu(query):
    """Поиск товаров"""
    if USE_REAL_MENU:
        return search_items(query)
    else:
        results = []
        query_lower = query.lower()
        for cat_items in TEST_MENU.values():
            for item in cat_items:
                if query_lower in item["name"].lower():
                    results.append(item)
        return results

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
    
    keyboard = create_main_keyboard()
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"*MYC RESTAURANT*\n\n"
        f"Выберите кухню:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    logger.info(f"Пользователь {user_id} запустил бота")

@dp.callback_query(lambda c: c.data.startswith("cat_"))
async def show_category(call: types.CallbackQuery):
    """Показать категорию"""
    cat_id = call.data[4:]  # cat_burgers -> burgers
    
    items = get_items_by_category(cat_id)
    
    if not items:
        await call.answer("В этой категории пока нет товаров")
        return
    
    cat_name = CUISINES.get(cat_id, "Категория")
    
    # Создаем кнопки товаров
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
    
    item = find_item(item_id)
    
    if not item:
        await call.answer("Товар не найден")
        return
    
    # Формируем описание
    description = f"*{item['name']}*\n\n{item.get('description', '')}\n"
    
    # Добавляем детали
    if 'weight' in item:
        description += f"⚖️ Вес: {item['weight']}\n"
    if 'size' in item:
        description += f"📏 Размер: {item['size']}\n"
    if 'pieces' in item:
        description += f"🔢 Количество: {item['pieces']}\n"
    
    description += f"\n💰 *Цена: {item['price']}₽*"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"➕ Добавить в корзину ({item['price']}₽)", callback_data=f"add_{item_id}")],
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
    
    item = find_item(item_id)
    
    if not item:
        await call.answer("Товар не найден")
        return
    
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
    items = user_cart[user_id]
    
    if not items:
        text = "*🛒 Корзина пуста*\n\nДобавьте товары из меню!"
        keyboard = [[InlineKeyboardButton(text="📋 К меню", callback_data="back")]]
    else:
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
    items = user_cart.get(user_id, [])
    
    if not items:
        await call.answer("Корзина пуста!", show_alert=True)
        return
    
    total = sum(item["price"] for item in items)
    count = len(items)
    
    # Очищаем корзину
    user_cart[user_id].clear()
    
    await call.message.edit_text(
        f"✅ *Заказ принят!*\n\n"
        f"📦 Позиций: {count}\n"
        f"💰 Сумма: {total}₽\n\n"
        f"Спасибо за заказ! 🎉\n"
        f"Ожидайте звонка оператора.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Новый заказ", callback_data="back")]
        ]),
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
    
    if text in ["меню", "menu", "start", "/start"]:
        keyboard = create_main_keyboard()
        await message.answer(
            "*MYC RESTAURANT*\n\nВыберите кухню:",
            reply_markup=keyboard,
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
    
    # Поиск товаров
    if len(text) > 2:
        results = search_items_in_menu(text)
        if results:
            response = "🔍 *Найденные товары:*\n\n"
            for item in results[:5]:
                response += f"• {item['name']} - {item['price']}₽\n"
            response += "\nИспользуйте кнопки меню для заказа."
            await message.answer(response, parse_mode="Markdown")
            return
    
    # Стандартный ответ
    await message.answer(
        "🤖 Используйте кнопки меню или напишите:\n\n"
        "• **Меню** - показать кухни\n"
        "• **Корзина** - посмотреть корзину\n"
        "• **Название блюда** - поиск товара",
        parse_mode="Markdown"
    )

async def main():
    """Главная функция"""
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК MYC RESTAURANT БОТА")
    logger.info(f"Используется меню: {'РЕАЛЬНОЕ' if USE_REAL_MENU else 'ТЕСТОВОЕ'}")
    logger.info(f"Доступные кухни: {list(CUISINES.keys())}")
    logger.info("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

