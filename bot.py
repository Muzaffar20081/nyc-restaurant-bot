# pro_bot.py — ПРОФЕССИОНАЛЬНЫЙ БОТ ДЛЯ РЕСТОРАНА
import asyncio
import os
import sys
import logging
from collections import defaultdict
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InputMediaPhoto
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Импортируем конфиг
try:
    from config import BOT_TOKEN, CUISINES
    logger.info(f"✅ Конфиг загружен: {len(CUISINES)} кухонь")
except ImportError as e:
    logger.error(f"❌ Ошибка загрузки config.py: {e}")
    sys.exit(1)

# Импортируем меню
try:
    from menu import get_menu_by_category, find_item_by_id, search_items
    logger.info("✅ Реальное меню загружено")
except ImportError as e:
    logger.error(f"❌ Ошибка загрузки меню: {e}")
    sys.exit(1)

# Инициализация бота с настройками
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.MARKDOWN,
        link_preview_is_disabled=True
    )
)
dp = Dispatcher()

# Хранилища данных
user_cart = defaultdict(list)  # Корзина пользователей
user_data = defaultdict(dict)  # Дополнительные данные пользователей
order_history = defaultdict(list)  # История заказов

# Статистика
bot_stats = {
    "start_time": datetime.now(),
    "total_users": set(),
    "total_orders": 0,
    "total_revenue": 0
}

def create_main_keyboard():
    """Создает главное меню с категориями"""
    keyboard = []
    
    # Создаем кнопки категорий
    for cuisine_id, cuisine_name in CUISINES.items():
        keyboard.append([
            InlineKeyboardButton(
                text=cuisine_name,
                callback_data=f"cat_{cuisine_id}"
            )
        ])
    
    # Нижний ряд кнопок
    keyboard.append([
        InlineKeyboardButton(text="🛒 Корзина", callback_data="view_cart"),
        InlineKeyboardButton(text="⭐ Избранное", callback_data="favorites"),
        InlineKeyboardButton(text="📞 Помощь", callback_data="help")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_item_keyboard(item_id, item_price, category_id, is_favorite=False):
    """Создает клавиатуру для товара"""
    favorite_icon = "❤️" if is_favorite else "🤍"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"➕ В корзину", callback_data=f"add_{item_id}"),
            InlineKeyboardButton(text=favorite_icon, callback_data=f"fav_{item_id}")
        ],
        [
            InlineKeyboardButton(text="📋 В меню", callback_data="main_menu"),
            InlineKeyboardButton(text="🛒 Корзина", callback_data="view_cart")
        ]
    ])

@dp.message(CommandStart())
async def start_command(message: types.Message):
    """Главная команда /start"""
    user_id = message.from_user.id
    username = message.from_user.username or "Без имени"
    
    # Сохраняем статистику
    bot_stats["total_users"].add(user_id)
    
    logger.info(f"👤 Новый пользователь: {username} (ID: {user_id})")
    
    # Приветственное сообщение
    welcome_text = (
        f"👋 *Добро пожаловать, {message.from_user.first_name}!*\n\n"
        f"🍽️ *MYC RESTAURANT* — лучшая еда с доставкой!\n\n"
        f"🔥 *Спецпредложение:* Первый заказ со скидкой 15%!\n"
        f"🚚 *Бесплатная доставка* при заказе от 1000₽\n"
        f"⏰ *Работаем:* 10:00 - 23:00 ежедневно\n\n"
        f"Выберите кухню:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=create_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(Command("menu"))
async def menu_command(message: types.Message):
    """Команда /menu"""
    await message.answer(
        "🍽️ *Наше меню*\n\nВыберите кухню:",
        reply_markup=create_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(Command("cart"))
async def cart_command(message: types.Message):
    """Команда /cart"""
    await show_cart_message(message)

@dp.message(Command("help"))
async def help_command(message: types.Message):
    """Команда /help"""
    help_text = (
        "📞 *Помощь и поддержка*\n\n"
        "• /start — начать работу с ботом\n"
        "• /menu — открыть меню\n"
        "• /cart — посмотреть корзину\n"
        "• /help — эта справка\n\n"
        "📱 *Как сделать заказ:*\n"
        "1. Выберите кухню\n"
        "2. Добавьте блюда в корзину\n"
        "3. Перейдите в корзину\n"
        "4. Оформите заказ\n\n"
        "📞 *Контакты:*\n"
        "• Телефон: +7 (999) 123-45-67\n"
        "• Доставка: 30-60 минут\n"
        "• Оплата: карта/наличные\n\n"
        "💬 *Напишите нам, если есть вопросы!*"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Открыть меню", callback_data="main_menu")],
        [InlineKeyboardButton(text="🛒 Моя корзина", callback_data="view_cart")]
    ])
    
    await message.answer(help_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    """Команда /stats (только для админа)"""
    user_id = message.from_user.id
    
    # Проверяем админа (можно добавить список админов в config.py)
    if user_id != 123456789:  # Замените на ваш ID
        await message.answer("⛔ Эта команда только для администраторов")
        return
    
    uptime = datetime.now() - bot_stats["start_time"]
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    
    stats_text = (
        "📊 *Статистика бота*\n\n"
        f"• 🕐 Работает: {uptime.days}д {hours}ч {minutes}м\n"
        f"• 👥 Пользователей: {len(bot_stats['total_users'])}\n"
        f"• 📦 Заказов: {bot_stats['total_orders']}\n"
        f"• 💰 Выручка: {bot_stats['total_revenue']}₽\n"
        f"• 🍔 Кухонь: {len(CUISINES)}\n\n"
        f"🔄 Последнее обновление: {datetime.now().strftime('%H:%M:%S')}"
    )
    
    await message.answer(stats_text, parse_mode="Markdown")

@dp.callback_query(F.data == "main_menu")
async def main_menu_callback(call: types.CallbackQuery):
    """Возврат в главное меню"""
    await call.message.edit_text(
        "🍽️ *MYC RESTAURANT*\n\nВыберите кухню:",
        reply_markup=create_main_keyboard(),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def category_callback(call: types.CallbackQuery):
    """Обработка выбора категории"""
    try:
        cat_id = call.data[4:]
        cat_name = CUISINES.get(cat_id, "Категория")
        
        items = get_menu_by_category(cat_id)
        
        if not items:
            await call.answer("😔 В этой категории пока нет товаров", show_alert=True)
            return
        
        # Создаем клавиатуру с товарами
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
            f"*{cat_name}*\n\n🍴 Выберите блюдо:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в category_callback: {e}")
        await call.answer("⚠️ Ошибка загрузки категории")

@dp.callback_query(F.data.startswith("item_"))
async def item_callback(call: types.CallbackQuery):
    """Просмотр товара"""
    try:
        item_id = call.data[5:]
        user_id = call.from_user.id
        
        item = find_item_by_id(item_id)
        
        if not item:
            await call.answer("❌ Товар не найден", show_alert=True)
            return
        
        # Форматируем описание
        description = f"*{item['name']}*\n\n{item.get('description', '')}\n"
        
        # Добавляем характеристики
        details = []
        if 'weight' in item:
            details.append(f"⚖️ Вес: {item['weight']}")
        if 'size' in item:
            details.append(f"📏 Размер: {item['size']}")
        if 'pieces' in item:
            details.append(f"🔢 Количество: {item['pieces']}")
        
        if details:
            description += "\n" + "\n".join(details) + "\n"
        
        description += f"\n💰 *Цена: {item['price']}₽*\n"
        
        # Проверяем, есть ли в избранном
        is_favorite = item_id in user_data[user_id].get('favorites', [])
        
        await call.message.edit_text(
            description,
            reply_markup=create_item_keyboard(item_id, item['price'], item['category'], is_favorite),
            parse_mode="Markdown"
        )
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в item_callback: {e}")
        await call.answer("⚠️ Ошибка загрузки товара")

@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart_callback(call: types.CallbackQuery):
    """Добавление в корзину"""
    try:
        item_id = call.data[4:]
        user_id = call.from_user.id
        
        item = find_item_by_id(item_id)
        
        if not item:
            await call.answer("❌ Товар не найден", show_alert=True)
            return
        
        # Добавляем товар в корзину
        user_cart[user_id].append(item)
        
        # Обновляем статистику
        logger.info(f"🛒 {user_id} добавил {item['name']} за {item['price']}₽")
        
        await call.answer(
            f"✅ {item['name']} добавлен в корзину!\n💰 +{item['price']}₽",
            show_alert=True
        )
        
        # Возвращаемся к категории
        call.data = f"cat_{item['category']}"
        await category_callback(call)
        
    except Exception as e:
        logger.error(f"Ошибка в add_to_cart_callback: {e}")
        await call.answer("⚠️ Ошибка добавления в корзину")

@dp.callback_query(F.data.startswith("fav_"))
async def favorite_callback(call: types.CallbackQuery):
    """Добавление/удаление из избранного"""
    try:
        item_id = call.data[4:]
        user_id = call.from_user.id
        
        # Инициализируем избранное если нужно
        if 'favorites' not in user_data[user_id]:
            user_data[user_id]['favorites'] = []
        
        favorites = user_data[user_id]['favorites']
        
        if item_id in favorites:
            favorites.remove(item_id)
            action = "удалён из"
            icon = "🤍"
        else:
            favorites.append(item_id)
            action = "добавлен в"
            icon = "❤️"
        
        await call.answer(f"⭐ Товар {action} избранное", show_alert=False)
        
        # Обновляем кнопку
        item = find_item_by_id(item_id)
        if item:
            await call.message.edit_reply_markup(
                reply_markup=create_item_keyboard(
                    item_id, 
                    item['price'], 
                    item['category'], 
                    item_id in favorites
                )
            )
        
    except Exception as e:
        logger.error(f"Ошибка в favorite_callback: {e}")
        await call.answer("⚠️ Ошибка")

@dp.callback_query(F.data == "view_cart")
async def view_cart_callback(call: types.CallbackQuery):
    """Просмотр корзины"""
    await show_cart(call)

async def show_cart_message(message: types.Message):
    """Показать корзину в ответ на сообщение"""
    user_id = message.from_user.id
    items = user_cart[user_id]
    
    if not items:
        response = "*🛒 Ваша корзина пуста*\n\n"
        response += "Добавьте товары из меню, чтобы сделать заказ! 🍔"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Открыть меню", callback_data="main_menu")]
        ])
        
        await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")
        return
    
    # Формируем содержимое корзины
    cart_text, total = format_cart(items)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Ещё товары", callback_data="main_menu"),
            InlineKeyboardButton(text="🗑️ Очистить", callback_data="clear_cart")
        ],
        [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton(text="📱 Связаться", callback_data="contact")]
    ])
    
    await message.answer(cart_text, reply_markup=keyboard, parse_mode="Markdown")

async def show_cart(call: types.CallbackQuery):
    """Показать корзину в callback"""
    user_id = call.from_user.id
    items = user_cart[user_id]
    
    if not items:
        response = "*🛒 Ваша корзина пуста*\n\n"
        response += "Добавьте товары из меню, чтобы сделать заказ! 🍔"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Открыть меню", callback_data="main_menu")]
        ])
        
        await call.message.edit_text(response, reply_markup=keyboard, parse_mode="Markdown")
        await call.answer()
        return
    
    # Формируем содержимое корзины
    cart_text, total = format_cart(items)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Ещё товары", callback_data="main_menu"),
            InlineKeyboardButton(text="🗑️ Очистить", callback_data="clear_cart")
        ],
        [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton(text="📱 Связаться", callback_data="contact")]
    ])
    
    await call.message.edit_text(cart_text, reply_markup=keyboard, parse_mode="Markdown")
    await call.answer()

def format_cart(items):
    """Форматирует содержимое корзины"""
    total = 0
    counts = {}
    
    for item in items:
        name = item['name']
        price = item['price']
        
        if name in counts:
            counts[name]['count'] += 1
            counts[name]['total'] += price
        else:
            counts[name] = {
                'price': price,
                'count': 1,
                'total': price
            }
        
        total += price
    
    # Формируем текст
    cart_text = "*🛒 Ваша корзина:*\n\n"
    
    for name, data in counts.items():
        cart_text += f"• {name}\n"
        cart_text += f"  └ {data['count']} × {data['price']}₽ = {data['total']}₽\n"
    
    cart_text += f"\n📦 *Итого позиций:* {len(items)}"
    cart_text += f"\n💰 *Сумма заказа:* {total}₽\n"
    
    # Проверяем на бесплатную доставку
    if total < 1000:
        cart_text += f"\n🚚 *Добавьте ещё {1000 - total}₽ для бесплатной доставки!*"
    else:
        cart_text += f"\n🎉 *Бесплатная доставка!*"
    
    return cart_text, total

@dp.callback_query(F.data == "clear_cart")
async def clear_cart_callback(call: types.CallbackQuery):
    """Очистка корзины"""
    user_id = call.from_user.id
    
    if user_id in user_cart and user_cart[user_id]:
        item_count = len(user_cart[user_id])
        user_cart[user_id].clear()
        
        logger.info(f"🗑️ {user_id} очистил корзину ({item_count} товаров)")
        
        await call.answer(f"🗑️ Корзина очищена! Удалено {item_count} товаров", show_alert=True)
    else:
        await call.answer("🛒 Корзина уже пуста!", show_alert=True)
    
    await show_cart(call)

@dp.callback_query(F.data == "checkout")
async def checkout_callback(call: types.CallbackQuery):
    """Оформление заказа"""
    user_id = call.from_user.id
    items = user_cart.get(user_id, [])
    
    if not items:
        await call.answer("🛒 Корзина пуста!", show_alert=True)
        return
    
    total = sum(item["price"] for item in items)
    item_count = len(items)
    
    # Сохраняем в историю
    order = {
        "timestamp": datetime.now(),
        "items": items.copy(),
        "total": total,
        "user_id": user_id
    }
    order_history[user_id].append(order)
    
    # Обновляем статистику
    bot_stats["total_orders"] += 1
    bot_stats["total_revenue"] += total
    
    # Очищаем корзину
    user_cart[user_id].clear()
    
    # Формируем детали заказа
    order_details = f"✅ *Заказ №{bot_stats['total_orders']} принят!*\n\n"
    order_details += f"📅 *Дата:* {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    order_details += f"👤 *Клиент:* {call.from_user.first_name}\n"
    order_details += f"📦 *Позиций:* {item_count}\n"
    order_details += f"💰 *Сумма:* {total}₽\n\n"
    
    # Считаем уникальные товары для краткости
    unique_items = {}
    for item in items:
        name = item['name']
        unique_items[name] = unique_items.get(name, 0) + 1
    
    order_details += "*Состав заказа:*\n"
    for name, count in list(unique_items.items())[:5]:  # Первые 5 позиций
        order_details += f"• {name} ×{count}\n"
    
    if len(unique_items) > 5:
        order_details += f"• ...и ещё {len(unique_items) - 5} позиций\n"
    
    order_details += "\n📞 *С вами свяжется оператор в течение 5 минут*\n"
    order_details += "🚚 *Доставка:* 30-60 минут\n"
    order_details += "💳 *Оплата:* при получении\n\n"
    order_details += "🍽️ *Приятного аппетита!*\n"
    order_details += "⭐ *Оцените заказ после получения!*"
    
    logger.info(f"✅ Заказ #{bot_stats['total_orders']} от {user_id} на {total}₽")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Новый заказ", callback_data="main_menu")],
        [InlineKeyboardButton(text="📞 Поддержка", callback_data="contact")]
    ])
    
    await call.message.edit_text(
        order_details,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(F.data == "contact")
async def contact_callback(call: types.CallbackQuery):
    """Контакты"""
    contact_text = (
        "📞 *Контакты MYC RESTAURANT*\n\n"
        "• 📱 Телефон: +7 (999) 123-45-67\n"
        "• 📍 Адрес: ул. Примерная, д. 1\n"
        "• 🕐 Часы работы: 10:00 - 23:00\n"
        "• 🚚 Доставка: 30-60 минут\n\n"
        "💬 *Напишите нам, если есть вопросы!*\n"
        "Мы всегда рады помочь! 😊"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Вернуться в меню", callback_data="main_menu")],
        [InlineKeyboardButton(text="🛒 Моя корзина", callback_data="view_cart")]
    ])
    
    await call.message.edit_text(
        contact_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(F.data == "favorites")
async def favorites_callback(call: types.CallbackQuery):
    """Избранное"""
    user_id = call.from_user.id
    favorites = user_data[user_id].get('favorites', [])
    
    if not favorites:
        response = "⭐ *У вас пока нет избранных товаров*\n\n"
        response += "Добавляйте товары в избранное, нажимая ❤️\n"
        response += "Это поможет быстро находить любимые блюда!"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Открыть меню", callback_data="main_menu")]
        ])
        
        await call.message.edit_text(response, reply_markup=keyboard, parse_mode="Markdown")
        await call.answer()
        return
    
    # Получаем информацию о товарах
    favorite_items = []
    for item_id in favorites:
        item = find_item_by_id(item_id)
        if item:
            favorite_items.append(item)
    
    if not favorite_items:
        response = "⭐ *Избранные товары не найдены*\n\n"
        response += "Возможно, они были удалены из меню."
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Открыть меню", callback_data="main_menu")]
        ])
        
        await call.message.edit_text(response, reply_markup=keyboard, parse_mode="Markdown")
        await call.answer()
        return
    
    # Формируем список
    response = "⭐ *Ваши избранные товары:*\n\n"
    
    keyboard = []
    for item in favorite_items:
        emoji = item.get('image', '🍽️')
        keyboard.append([
            InlineKeyboardButton(
                text=f"{emoji} {item['name']} - {item['price']}₽",
                callback_data=f"item_{item['id']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="view_cart")
    ])
    
    await call.message.edit_text(
        response,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(F.data == "help")
async def help_callback(call: types.CallbackQuery):
    """Помощь в callback"""
    help_text = (
        "🤖 *Помощь по боту*\n\n"
        "🍔 *Как сделать заказ:*\n"
        "1. Выберите кухню\n"
        "2. Добавьте товары в корзину\n"
        "3. Перейдите в корзину\n"
        "4. Оформите заказ\n\n"
        "⭐ *Избранное:*\n"
        "Нажимайте ❤️ на товарах, чтобы добавить в избранное\n\n"
        "📞 *Контакты поддержки:*\n"
        "+7 (999) 123-45-67\n\n"
        "⏰ *Часы работы:*\n"
        "10:00 - 23:00 ежедневно"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Открыть меню", callback_data="main_menu")],
        [InlineKeyboardButton(text="🛒 Моя корзина", callback_data="view_cart")]
    ])
    
    await call.message.edit_text(
        help_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await call.answer()

@dp.message(F.text)
async def text_handler(message: types.Message):
    """Обработчик текстовых сообщений"""
    text = message.text.strip().lower()
    user_id = message.from_user.id
    
    logger.info(f"💬 {user_id}: {text}")
    
    # Поиск товаров
    if len(text) > 2:
        results = search_items(text)
        if results:
            response = "🔍 *По вашему запросу найдено:*\n\n"
            
            keyboard = []
            for item in results[:5]:  # Ограничиваем 5 результатами
                emoji = item.get('image', '🍽️')
                keyboard.append([
                    InlineKeyboardButton(
                        text=f"{emoji} {item['name']} - {item['price']}₽",
                        callback_data=f"item_{item['id']}"
                    )
                ])
            
            if len(results) > 5:
                response += f"*...и ещё {len(results) - 5} товаров*\n\n"
            
            response += "Нажмите на товар для подробностей"
            
            keyboard.append([
                InlineKeyboardButton(text="📋 Все меню", callback_data="main_menu"),
                InlineKeyboardButton(text="🛒 Корзина", callback_data="view_cart")
            ])
            
            await message.answer(
                response,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode="Markdown"
            )
            return
    
    # Обработка команд текстом
    commands = {
        "меню": "main_menu",
        "menu": "main_menu",
        "корзина": "view_cart",
        "cart": "view_cart",
        "заказ": "view_cart",
        "помощь": "help",
        "help": "help",
        "контакты": "contact",
        "контакт": "contact",
        "избранное": "favorites",
        "любимое": "favorites"
    }
    
    if text in commands:
        call = types.CallbackQuery(
            id="text_command",
            from_user=message.from_user,
            message=message,
            chat_instance="0",
            data=commands[text]
        )
        
        # Вызываем соответствующий обработчик
        handlers = {
            "main_menu": main_menu_callback,
            "view_cart": view_cart_callback,
            "help": help_callback,
            "contact": contact_callback,
            "favorites": favorites_callback
        }
        
        if commands[text] in handlers:
            await handlers[commands[text]](call)
        return
    
    # Стандартный ответ
    response = (
        "🤖 *MYC RESTAURANT Бот*\n\n"
        "Я помогу вам сделать заказ вкусной еды! 🍔\n\n"
        "*Основные команды:*\n"
        "• **Меню** — показать все кухни\n"
        "• **Корзина** — посмотреть корзину\n"
        "• **Помощь** — справка по боту\n"
        "• **Контакты** — наши контакты\n\n"
        "*Или просто напишите название блюда для поиска!* 🔍"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Открыть меню", callback_data="main_menu")],
        [InlineKeyboardButton(text="🛒 Моя корзина", callback_data="view_cart")]
    ])
    
    await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")

async def main():
    """Главная функция запуска"""
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК ПРОФЕССИОНАЛЬНОГО БОТА MYC RESTAURANT")
    logger.info(f"🤖 Бот ID: {BOT_TOKEN[:15]}...")
    logger.info(f"🍽️ Кухни: {list(CUISINES.keys())}")
    logger.info(f"⏰ Время запуска: {bot_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    try:
        # Удаляем вебхук на всякий случай
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаем опрос
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("🛑 Бот остановлен")
        await bot.session.close()

if __name__ == "__main__":
    # Проверяем зависимости
    try:
        import aiogram
        print(f"✅ aiogram версия: {aiogram.__version__}")
    except ImportError:
        print("❌ aiogram не установлен!")
        print("Установите: pip install aiogram")
        sys.exit(1)
    
    # Запускаем бота
    asyncio.run(main())
