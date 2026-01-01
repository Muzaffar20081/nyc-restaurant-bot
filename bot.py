# bot_final.py — ОКОНЧАТЕЛЬНЫЙ ИСПРАВЛЕННЫЙ КОД
import asyncio
import os
import sys
import logging
from collections import defaultdict

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# Импортируем меню
try:
    from menu import MENU_CATEGORIES, get_menu_by_category, find_item_by_id, search_items
    print("✅ Меню успешно импортировано")
except ImportError as e:
    print(f"❌ Ошибка импорта меню: {e}")
    print("Проверьте структуру папки menu/")
    sys.exit(1)

# Импортируем конфиг
try:
    from config import BOT_TOKEN, CUISINES
    print("✅ Конфиг успешно импортирован")
    
    # Обновляем категории из config.py если они там есть
    if CUISINES:
        print(f"✅ Найдены кухни в config.py: {CUISINES}")
        # Можно обновить MENU_CATEGORIES или использовать CUISINES
except ImportError as e:
    print(f"❌ Ошибка импорта config.py: {e}")
    print("Создайте файл config.py с BOT_TOKEN и CUISINES")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверяем токен
if not BOT_TOKEN:
    logger.error("❌ Токен не найден в config.py!")
    sys.exit(1)

# Инициализация
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.MARKDOWN)
dp = Dispatcher()

# Хранилища
user_cart = defaultdict(list)
user_states = {}

def create_main_menu():
    """Создает главное меню"""
    keyboard = []
    
    # Используем CUISINES из config.py для создания меню
    cuisines_list = list(CUISINES.items())
    
    # Добавляем категории по 2 в ряд
    for i in range(0, len(cuisines_list), 2):
        row = []
        if i < len(cuisines_list):
            cat_id, cat_name = cuisines_list[i]
            row.append(InlineKeyboardButton(
                text=cat_name,
                callback_data=f"cat_{cat_id}"
            ))
        if i + 1 < len(cuisines_list):
            cat_id, cat_name = cuisines_list[i + 1]
            row.append(InlineKeyboardButton(
                text=cat_name,
                callback_data=f"cat_{cat_id}"
            ))
        if row:
            keyboard.append(row)
    
    # Добавляем корзину
    keyboard.append([InlineKeyboardButton(text="🛒 Корзина", callback_data="view_cart")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(CommandStart())
async def start_command(message: types.Message):
    """Обработчик /start"""
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} запустил бота")
    
    # Создаем меню
    menu = create_main_menu()
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"*MYC RESTAURANT*\n\n"
        f"Выберите кухню:",
        reply_markup=menu
    )

@dp.callback_query(lambda c: c.data.startswith("cat_"))
async def category_handler(call: types.CallbackQuery):
    """Обработчик категорий"""
    category_id = call.data[4:]  # cat_burgers -> burgers
    
    # Получаем товары категории
    items = get_menu_by_category(category_id)
    
    if not items:
        await call.answer("В этой категории пока нет товаров")
        return
    
    # Находим название категории из CUISINES
    category_name = CUISINES.get(category_id, "Категория")
    
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
        InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="view_cart")
    ])
    
    await call.message.edit_text(
        f"*{category_name}*\n\nВыберите блюдо:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("item_"))
async def item_handler(call: types.CallbackQuery):
    """Обработчик товара"""
    item_id = call.data[5:]  # item_whopper -> whopper
    
    # Ищем товар
    item = find_item_by_id(item_id)
    
    if not item:
        await call.answer("Товар не найден")
        return
    
    # Формируем описание
    description = f"*{item['name']}*\n\n"
    description += f"{item.get('description', '')}\n"
    
    # Добавляем детали
    if 'weight' in item:
        description += f"⚖️ Вес: {item['weight']}\n"
    if 'size' in item:
        description += f"📏 Размер: {item['size']}\n"
    if 'pieces' in item:
        description += f"🔢 Количество: {item['pieces']}\n"
    
    description += f"\n💰 Цена: *{item['price']}₽*"
    
    # Создаем кнопки
    keyboard = [
        [InlineKeyboardButton(
            text=f"➕ Добавить в корзину ({item['price']}₽)",
            callback_data=f"add_{item_id}"
        )],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"cat_{item['category']}"),
            InlineKeyboardButton(text="🛒 Корзина", callback_data="view_cart")
        ]
    ]
    
    await call.message.edit_text(
        description,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart_handler(call: types.CallbackQuery):
    """Добавить в корзину"""
    item_id = call.data[4:]  # add_whopper -> whopper
    item = find_item_by_id(item_id)
    
    if not item:
        await call.answer("Товар не найден")
        return
    
    user_id = call.from_user.id
    user_cart[user_id].append(item)
    
    await call.answer(f"✅ {item['name']} добавлен в корзину!", show_alert=True)
    
    # Возвращаемся к категории
    call.data = f"cat_{item['category']}"
    await category_handler(call)

@dp.callback_query(lambda c: c.data == "view_cart")
async def view_cart_handler(call: types.CallbackQuery):
    """Показать корзину"""
    user_id = call.from_user.id
    items = user_cart[user_id]
    
    if not items:
        text = "*🛒 Корзина пуста*\n\nДобавьте товары из меню!"
        keyboard = [[InlineKeyboardButton(text="📋 К меню", callback_data="main_menu")]]
    else:
        # Считаем товары
        counts = {}
        total = 0
        
        for item in items:
            name = item['name']
            if name in counts:
                counts[name]['count'] += 1
                counts[name]['total'] += item['price']
            else:
                counts[name] = {
                    'price': item['price'],
                    'count': 1,
                    'total': item['price']
                }
            total += item['price']
        
        # Формируем текст
        text = "*🛒 Ваша корзина:*\n\n"
        for name, data in counts.items():
            text += f"• {name} ×{data['count']} = {data['total']}₽\n"
        
        text += f"\n💰 *Итого: {total}₽*"
        
        # Создаем кнопки
        keyboard = [
            [InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="📋 Продолжить покупки", callback_data="main_menu")]
        ]
    
    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart_handler(call: types.CallbackQuery):
    """Очистить корзину"""
    user_id = call.from_user.id
    if user_id in user_cart:
        user_cart[user_id].clear()
        await call.answer("Корзина очищена!", show_alert=True)
    
    await view_cart_handler(call)

@dp.callback_query(lambda c: c.data == "checkout")
async def checkout_handler(call: types.CallbackQuery):
    """Оформить заказ"""
    user_id = call.from_user.id
    items = user_cart.get(user_id, [])
    
    if not items:
        await call.answer("Корзина пуста!", show_alert=True)
        return
    
    # Считаем сумму
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
            [InlineKeyboardButton(text="📋 Новый заказ", callback_data="main_menu")]
        ])
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "main_menu")
async def main_menu_handler(call: types.CallbackQuery):
    """Вернуться в главное меню"""
    menu = create_main_menu()
    
    await call.message.edit_text(
        "*MYC RESTAURANT*\n\nВыберите кухню:",
        reply_markup=menu
    )
    await call.answer()

@dp.message()
async def text_handler(message: types.Message):
    """Обработчик текстовых сообщений"""
    if not message.text:
        return
    
    user_text = message.text.strip().lower()
    
    # Команды
    if user_text in ["меню", "menu", "start", "/start"]:
        menu = create_main_menu()
        await message.answer(
            "*MYC RESTAURANT*\n\nВыберите кухню:",
            reply_markup=menu
        )
        return
    
    if user_text in ["корзина", "cart"]:
        user_id = message.from_user.id
        items = user_cart[user_id]
        
        if not items:
            await message.answer("*🛒 Корзина пуста!*")
            return
        
        # Показываем корзину
        counts = {}
        total = 0
        
        for item in items:
            name = item['name']
            if name in counts:
                counts[name]['count'] += 1
                counts[name]['total'] += item['price']
            else:
                counts[name] = {'price': item['price'], 'count': 1, 'total': item['price']}
            total += item['price']
        
        text_response = "*🛒 Ваша корзина:*\n\n"
        for name, data in counts.items():
            text_response += f"• {name} ×{data['count']} = {data['total']}₽\n"
        
        text_response += f"\n💰 *Итого: {total}₽*"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ Очистить", callback_data="clear_cart")],
            [InlineKeyboardButton(text="✅ Оформить", callback_data="checkout")],
            [InlineKeyboardButton(text="📋 К меню", callback_data="main_menu")]
        ])
        
        await message.answer(text_response, reply_markup=keyboard)
        return
    
    # Поиск
    if len(user_text) > 2:
        results = search_items(user_text)
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
    logger.info("=" * 50)
    logger.info(f"Используется токен: {BOT_TOKEN[:10]}...")
    logger.info(f"Доступные кухни: {list(CUISINES.keys())}")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())
