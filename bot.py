# final_working_bot.py
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
    print(f"📋 Кухни: {CUISINES}")
except ImportError as e:
    print(f"❌ Ошибка config.py: {e}")
    sys.exit(1)

# Загружаем реальное меню
try:
    from menu import get_menu_by_category, find_item_by_id, search_items
    print(f"✅ Реальное меню загружено")
    
    # Тестируем меню
    print("🧪 Тест меню:")
    for cuisine in CUISINES:
        items = get_menu_by_category(cuisine)
        print(f"   {cuisine}: {len(items)} товаров")
        
except ImportError as e:
    print(f"❌ Ошибка загрузки меню: {e}")
    print("   Убедитесь, что папка 'menu' содержит:")
    print("   - __init__.py")
    print("   - burger_menu.py")
    print("   - italy_menu.py")
    print("   - sushi_menu.py")
    sys.exit(1)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
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
        reply_markup=menu,
        parse_mode="Markdown"
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
        emoji = item.get('image', '🍽️')
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
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
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
    description = f"*{item['name']}*\n\n{item.get('description', '')}\n"
    
    if 'weight' in item:
        description += f"⚖️ Вес: {item['weight']}\n"
    if 'size' in item:
        description += f"📏 Размер: {item['size']}\n"
    if 'pieces' in item:
        description += f"🔢 Количество: {item['pieces']}\n"
    
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
        reply_markup=keyboard,
        parse_mode="Markdown"
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
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
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
        ]),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "back")
async def back_callback(call: types.CallbackQuery):
    """Вернуться в меню"""
    menu = create_main_menu()
    
    await call.message.edit_text(
        "*MYC RESTAURANT*\n\nВыберите кухню:",
        reply_markup=menu,
        parse_mode="Markdown"
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
        
        await message.answer(text_response, reply_markup=keyboard, parse_mode="Markdown")
        return
    
    # Поиск товаров
    if len(text) > 2:
        results = search_items(text)
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
