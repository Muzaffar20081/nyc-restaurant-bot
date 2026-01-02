# myc_restaurant_bot.py — ФИНАЛЬНЫЙ РАБОЧИЙ БОТ
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

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен
try:
    from config import BOT_TOKEN, CUISINES
    print(f"✅ Токен загружен")
    print(f"📋 Кухни: {list(CUISINES.keys())}")
except ImportError as e:
    print(f"❌ Ошибка config.py: {e}")
    sys.exit(1)

# Создаем простое меню на основе CUISINES
def create_simple_menu():
    """Создает простое меню на основе кухонь из config.py"""
    menu = {}
    
    for cuisine_id in CUISINES:
        if cuisine_id == "burgers":
            menu[cuisine_id] = [
                {"id": "whopper", "name": "Воппер", "price": 299, "description": "Классический бургер", "category": "burgers"},
                {"id": "cheeseburger", "name": "Чизбургер", "price": 199, "description": "С сыром", "category": "burgers"},
                {"id": "big_mac", "name": "Биг Мак", "price": 259, "description": "Двойной бургер", "category": "burgers"},
            ]
        elif cuisine_id == "italy":
            menu[cuisine_id] = [
                {"id": "margarita", "name": "Маргарита", "price": 499, "description": "Классическая пицца", "category": "italy"},
                {"id": "pepperoni", "name": "Пепперони", "price": 549, "description": "Острая пицца", "category": "italy"},
                {"id": "carbonara", "name": "Карбонара", "price": 479, "description": "Паста карбонара", "category": "italy"},
            ]
        elif cuisine_id == "sushi":
            menu[cuisine_id] = [
                {"id": "philadelphia", "name": "Филадельфия", "price": 399, "description": "Ролл с лососем", "category": "sushi"},
                {"id": "california", "name": "Калифорния", "price": 359, "description": "Ролл с крабом", "category": "sushi"},
                {"id": "dragon_roll", "name": "Дракон ролл", "price": 459, "description": "Ролл с угрем", "category": "sushi"},
            ]
        else:
            # Для других кухонь создаем примерные товары
            menu[cuisine_id] = [
                {"id": f"{cuisine_id}_1", "name": f"Блюдо 1 ({cuisine_id})", "price": 299, "description": "Вкусное блюдо", "category": cuisine_id},
                {"id": f"{cuisine_id}_2", "name": f"Блюдо 2 ({cuisine_id})", "price": 399, "description": "Очень вкусное блюдо", "category": cuisine_id},
            ]
    
    return menu

# Создаем меню
SIMPLE_MENU = create_simple_menu()

# Функции для работы с меню
def get_menu_by_category(category_id):
    """Получить товары категории"""
    return SIMPLE_MENU.get(category_id, [])

def find_item_by_id(item_id):
    """Найти товар по ID"""
    for items in SIMPLE_MENU.values():
        for item in items:
            if item["id"] == item_id:
                return item
    return None

def search_items(query):
    """Поиск товаров по названию"""
    results = []
    query_lower = query.lower()
    
    for items in SIMPLE_MENU.values():
        for item in items:
            if query_lower in item["name"].lower():
                results.append(item)
    
    return results

# Инициализация бота
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.MARKDOWN)
dp = Dispatcher()

# Корзина
user_cart = defaultdict(list)

def create_main_menu():
    """Создает главное меню"""
    keyboard = []
    
    # Создаем кнопки из CUISINES
    for cuisine_id, cuisine_name in CUISINES.items():
        keyboard.append([
            InlineKeyboardButton(
                text=cuisine_name,
                callback_data=f"cat_{cuisine_id}"
            )
        ])
    
    # Кнопка корзины
    keyboard.append([InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(CommandStart())
async def start_command(message: types.Message):
    """Команда /start"""
    user_id = message.from_user.id
    logger.info(f"👤 Пользователь {user_id} запустил бота")
    
    menu = create_main_menu()
    
    await message.answer(
        f"👋 *Привет, {message.from_user.first_name}!*\n\n"
        f"🍽️ *MYC RESTAURANT*\n\n"
        f"Выберите кухню:",
        reply_markup=menu
    )

@dp.callback_query(lambda c: c.data.startswith("cat_"))
async def category_callback(call: types.CallbackQuery):
    """Выбор категории"""
    cat_id = call.data[4:]  # cat_burgers -> burgers
    
    items = get_menu_by_category(cat_id)
    
    if not items:
        await call.answer("😔 В этой категории пока нет товаров")
        return
    
    cat_name = CUISINES.get(cat_id, "Категория")
    
    # Создаем кнопки товаров
    keyboard = []
    for item in items:
        emoji = "🍔" if cat_id == "burgers" else "🍕" if cat_id == "italy" else "🍣" if cat_id == "sushi" else "🍽️"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{emoji} {item['name']} - {item['price']}₽",
                callback_data=f"item_{item['id']}"
            )
        ])
    
    # Кнопки навигации
    keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="back"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")
    ])
    
    await call.message.edit_text(
        f"*{cat_name}*\n\nВыберите блюдо:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("item_"))
async def item_callback(call: types.CallbackQuery):
    """Просмотр товара"""
    item_id = call.data[5:]  # item_whopper -> whopper
    
    item = find_item_by_id(item_id)
    
    if not item:
        await call.answer("❌ Товар не найден")
        return
    
    # Формируем описание
    description = f"*{item['name']}*\n\n{item['description']}\n"
    description += f"\n💰 Цена: *{item['price']}₽*"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"➕ Добавить в корзину ({item['price']}₽)", callback_data=f"add_{item_id}")],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"cat_{item['category']}"),
            InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")
        ]
    ])
    
    await call.message.edit_text(
        description,
        reply_markup=keyboard
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_callback(call: types.CallbackQuery):
    """Добавить в корзину"""
    item_id = call.data[4:]  # add_whopper -> whopper
    user_id = call.from_user.id
    
    item = find_item_by_id(item_id)
    
    if not item:
        await call.answer("❌ Товар не найден")
        return
    
    # Добавляем в корзину
    user_cart[user_id].append(item)
    
    await call.answer(f"✅ {item['name']} добавлен в корзину!", show_alert=True)
    
    # Возвращаемся к категории
    call.data = f"cat_{item['category']}"
    await category_callback(call)

@dp.callback_query(lambda c: c.data == "cart")
async def cart_callback(call: types.CallbackQuery):
    """Показать корзину"""
    user_id = call.from_user.id
    items = user_cart[user_id]
    
    if not items:
        text = "*🛒 Корзина пуста*\n\nДобавьте товары из меню!"
        keyboard = [[InlineKeyboardButton(text="📋 Меню", callback_data="back")]]
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
            [InlineKeyboardButton(text="📋 Меню", callback_data="back")]
        ]
    
    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart_callback(call: types.CallbackQuery):
    """Очистить корзину"""
    user_id = call.from_user.id
    if user_id in user_cart:
        user_cart[user_id].clear()
        await call.answer("🗑️ Корзина очищена!", show_alert=True)
    
    await cart_callback(call)

@dp.callback_query(lambda c: c.data == "checkout")
async def checkout_callback(call: types.CallbackQuery):
    """Оформить заказ"""
    user_id = call.from_user.id
    items = user_cart.get(user_id, [])
    
    if not items:
        await call.answer("🛒 Корзина пуста!", show_alert=True)
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
        ])
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "back")
async def back_callback(call: types.CallbackQuery):
    """Вернуться в меню"""
    menu = create_main_menu()
    
    await call.message.edit_text(
        "*MYC RESTAURANT*\n\nВыберите кухню:",
        reply_markup=menu
    )
    await call.answer()

@dp.message()
async def text_handler(message: types.Message):
    """Обработчик текстовых сообщений"""
    text = message.text.strip().lower()
    
    if text in ["меню", "menu", "start"]:
        menu = create_main_menu()
        await message.answer(
            "*MYC RESTAURANT*\n\nВыберите кухню:",
            reply_markup=menu
        )
        return
    
    if text in ["корзина", "cart"]:
        user_id = message.from_user.id
        items = user_cart[user_id]
        
        if not items:
            await message.answer("*🛒 Корзина пуста!*")
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
            [InlineKeyboardButton(text="📋 Меню", callback_data="back")]
        ])
        
        await message.answer(text_response, reply_markup=keyboard)
        return
    
    # Поиск товаров
    if len(text) > 2:
        results = search_items(text)
        if results:
            response = "🔍 *Найденные товары:*\n\n"
            for item in results[:5]:
                response += f"• {item['name']} - {item['price']}₽\n"
            response += "\nИспользуйте кнопки меню для заказа."
            await message.answer(response)
            return
    
    # Стандартный ответ
    await message.answer(
        "🤖 Используйте кнопки меню или напишите:\n\n"
        "• **Меню** - показать кухни\n"
        "• **Корзина** - посмотреть корзину\n"
        "• **Название блюда** - поиск товара"
    )

async def main():
    """Главная функция"""
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК MYC RESTAURANT БОТА")
    logger.info(f"🍽️ Кухни: {list(CUISINES.keys())}")
    logger.info("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
