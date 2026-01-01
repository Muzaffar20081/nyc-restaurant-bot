# bot.py — ПОЛНОСТЬЮ РАБОЧАЯ ВЕРСИЯ
import asyncio
import os
import logging
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Импортируем из папки menu
from menu import MENU_CATEGORIES, get_menu_by_category, find_item_by_id, search_items

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверяем токен
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("Токен не найден! Создайте файл .env с BOT_TOKEN=ваш_токен")
    exit(1)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

# Хранилища данных
user_cart = defaultdict(list)  # {user_id: [item1, item2, ...]}
user_states = {}  # {user_id: {"category": "burgers"}}

def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру главного меню"""
    keyboard = []
    
    # Добавляем кнопки категорий
    for i in range(0, len(MENU_CATEGORIES), 2):
        row = []
        if i < len(MENU_CATEGORIES):
            cat1 = MENU_CATEGORIES[i]
            row.append(InlineKeyboardButton(
                text=cat1["name"],
                callback_data=f"category_{cat1['id']}"
            ))
        if i + 1 < len(MENU_CATEGORIES):
            cat2 = MENU_CATEGORIES[i + 1]
            row.append(InlineKeyboardButton(
                text=cat2["name"],
                callback_data=f"category_{cat2['id']}"
            ))
        if row:
            keyboard.append(row)
    
    # Кнопка корзины
    keyboard.append([
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"),
        InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(CommandStart())
async def command_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    user_states[user_id] = {"category": None}
    
    logger.info(f"Пользователь {user_id} ({message.from_user.username}) запустил бота")
    
    keyboard = create_main_menu_keyboard()
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"*FOOD EXPRESS 2025*\n\n"
        f"Выберите категорию:",
        reply_markup=keyboard
    )

@dp.message(Command("menu"))
async def command_menu(message: types.Message):
    """Обработчик команды /menu"""
    keyboard = create_main_menu_keyboard()
    await message.answer(
        "*🍽️ Меню FOOD EXPRESS*\n\nВыберите категорию:",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "help")
async def callback_help(call: types.CallbackQuery):
    """Показать помощь"""
    help_text = (
        "ℹ️ *Помощь*\n\n"
        "• Используйте кнопки для навигации\n"
        "• Выбирайте товары из меню\n"
        "• Добавляйте товары в корзину\n"
        "• Оформляйте заказ через корзину\n\n"
        "📞 Телефон: +7 (999) 123-45-67\n"
        "⏰ Время работы: 10:00 - 23:00\n"
        "🚚 Доставка: 30-60 минут"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_categories")]
    ])
    
    await call.message.edit_text(
        help_text,
        reply_markup=keyboard
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("category_"))
async def callback_category(call: types.CallbackQuery):
    """Обработчик выбора категории"""
    category_id = call.data[9:]  # Убираем "category_"
    user_id = call.from_user.id
    
    # Сохраняем выбранную категорию
    if user_id not in user_states:
        user_states[user_id] = {}
    user_states[user_id]["category"] = category_id
    
    # Получаем товары категории
    menu_items = get_menu_by_category(category_id)
    
    if not menu_items:
        await call.answer("В этой категории пока нет товаров", show_alert=True)
        return
    
    # Создаем клавиатуру с товарами
    keyboard = []
    for item in menu_items:
        keyboard.append([InlineKeyboardButton(
            text=f"{item.get('image', '🍽️')} {item['name']} - {item['price']}₽",
            callback_data=f"item_{item['id']}"
        )])
    
    # Кнопки навигации
    keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_categories"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")
    ])
    
    # Находим название категории
    category_name = "Категория"
    for cat in MENU_CATEGORIES:
        if cat["id"] == category_id:
            category_name = cat["name"]
            break
    
    await call.message.edit_text(
        f"*{category_name}*\n\nВыберите блюдо:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("item_"))
async def callback_item(call: types.CallbackQuery):
    """Обработчик выбора товара"""
    item_id = call.data[5:]  # Убираем "item_"
    item = find_item_by_id(item_id)
    
    if not item:
        await call.answer("Товар не найден", show_alert=True)
        return
    
    # Формируем описание товара
    description = f"*{item['name']}*\n\n"
    description += f"{item.get('description', '')}\n\n"
    
    # Добавляем характеристики
    if 'weight' in item:
        description += f"⚖️ Вес: {item['weight']}\n"
    if 'size' in item:
        description += f"📏 Размер: {item['size']}\n"
    if 'pieces' in item:
        description += f"🔢 Количество: {item['pieces']}\n"
    
    description += f"\n💰 Цена: *{item['price']}₽*"
    
    # Создаем клавиатуру
    keyboard = [
        [InlineKeyboardButton(text=f"➕ Добавить в корзину ({item['price']}₽)", callback_data=f"add_{item_id}")],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"category_{item['category']}"),
            InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")
        ]
    ]
    
    await call.message.edit_text(
        description,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def callback_add(call: types.CallbackQuery):
    """Обработчик добавления в корзину"""
    item_id = call.data[4:]  # Убираем "add_"
    item = find_item_by_id(item_id)
    
    if not item:
        await call.answer("Товар не найден", show_alert=True)
        return
    
    user_id = call.from_user.id
    user_cart[user_id].append(item)
    
    logger.info(f"Пользователь {user_id} добавил в корзину: {item['name']}")
    
    await call.answer(f"✅ {item['name']} добавлен в корзину!", show_alert=True)
    
    # Возвращаемся к категории
    if 'category' in item:
        call.data = f"category_{item['category']}"
        await callback_category(call)

@dp.callback_query(lambda c: c.data == "cart")
async def callback_cart(call: types.CallbackQuery):
    """Обработчик корзины"""
    user_id = call.from_user.id
    items = user_cart[user_id]
    
    if not items:
        caption = "*🛒 Корзина пуста*\n\nДобавьте товары из меню!"
        keyboard = [[InlineKeyboardButton(text="📋 К меню", callback_data="back_to_categories")]]
    else:
        # Подсчитываем товары и сумму
        item_counts = {}
        total = 0
        
        for item in items:
            name = item['name']
            price = item['price']
            
            if name in item_counts:
                item_counts[name]['count'] += 1
                item_counts[name]['total'] += price
            else:
                item_counts[name] = {
                    'price': price,
                    'count': 1,
                    'total': price
                }
            
            total += price
        
        # Формируем текст корзины
        caption = "*🛒 Ваша корзина:*\n\n"
        for name, data in item_counts.items():
            caption += f"• {name} ×{data['count']} = {data['total']}₽\n"
        
        caption += f"\n💰 *Итого: {total}₽*"
        
        # Создаем клавиатуру
        keyboard = [
            [InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="📋 Продолжить покупки", callback_data="back_to_categories")]
        ]
    
    await call.message.edit_text(
        caption,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "clear_cart")
async def callback_clear_cart(call: types.CallbackQuery):
    """Обработчик очистки корзины"""
    user_id = call.from_user.id
    
    if user_id in user_cart and user_cart[user_id]:
        item_count = len(user_cart[user_id])
        user_cart[user_id].clear()
        logger.info(f"Пользователь {user_id} очистил корзину ({item_count} товаров)")
        await call.answer(f"🗑️ Корзина очищена! Удалено {item_count} товаров", show_alert=True)
    else:
        await call.answer("Корзина уже пуста!", show_alert=True)
    
    await callback_cart(call)

@dp.callback_query(lambda c: c.data == "checkout")
async def callback_checkout(call: types.CallbackQuery):
    """Обработчик оформления заказа"""
    user_id = call.from_user.id
    items = user_cart.get(user_id, [])
    
    if not items:
        await call.answer("Корзина пуста!", show_alert=True)
        return
    
    # Подсчет суммы и количества
    total = sum(item["price"] for item in items)
    item_count = len(items)
    
    # Формируем детали заказа
    order_details = "*✅ Заказ принят!*\n\n"
    order_details += f"📦 Количество позиций: {item_count}\n"
    order_details += f"💰 Сумма заказа: {total}₽\n\n"
    
    # Добавляем список товаров (первые 5)
    order_details += "*Состав заказа:*\n"
    item_counts = {}
    for item in items:
        name = item['name']
        item_counts[name] = item_counts.get(name, 0) + 1
    
    for name, count in list(item_counts.items())[:5]:
        order_details += f"• {name} ×{count}\n"
    
    if len(item_counts) > 5:
        order_details += f"• ...и ещё {len(item_counts) - 5} позиций\n"
    
    order_details += "\n📞 Скоро с вами свяжется оператор для подтверждения.\n"
    order_details += "🚚 Время доставки: 30-60 минут\n\n"
    order_details += "Спасибо за заказ! Приятного аппетита! 😊"
    
    # Логируем заказ
    logger.info(f"Пользователь {user_id} оформил заказ на {total}₽ ({item_count} товаров)")
    
    # Очищаем корзину
    user_cart[user_id].clear()
    
    # Показываем подтверждение
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Сделать новый заказ", callback_data="back_to_categories")]
    ])
    
    await call.message.edit_text(
        order_details,
        reply_markup=keyboard
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "back_to_categories")
async def callback_back(call: types.CallbackQuery):
    """Обработчик возврата к категориям"""
    keyboard = create_main_menu_keyboard()
    
    await call.message.edit_text(
        "*FOOD EXPRESS 2025*\n\nВыберите категорию:",
        reply_markup=keyboard
    )
    await call.answer()

@dp.message()
async def handle_text(message: types.Message):
    """Обработчик текстовых сообщений"""
    if not message.text:
        return
    
    text = message.text.strip()
    
    # Команды текстом
    if text.lower() in ["меню", "menu", "категории", "еда"]:
        keyboard = create_main_menu_keyboard()
        await message.answer(
            "*🍽️ Меню FOOD EXPRESS*\n\nВыберите категорию:",
            reply_markup=keyboard
        )
        return
    
    if text.lower() in ["корзина", "cart", "заказ", "мои покупки"]:
        user_id = message.from_user.id
        items = user_cart[user_id]
        
        if not items:
            await message.answer("*🛒 Корзина пуста!*\n\nДобавьте товары из меню!")
        else:
            item_counts = {}
            total = 0
            
            for item in items:
                name = item['name']
                price = item['price']
                
                if name in item_counts:
                    item_counts[name]['count'] += 1
                    item_counts[name]['total'] += price
                else:
                    item_counts[name] = {
                        'price': price,
                        'count': 1,
                        'total': price
                    }
                
                total += price
            
            caption = "*🛒 Ваша корзина:*\n\n"
            for name, data in item_counts.items():
                caption += f"• {name} ×{data['count']} = {data['total']}₽\n"
            
            caption += f"\n💰 *Итого: {total}₽*"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🗑️ Очистить", callback_data="clear_cart")],
                [InlineKeyboardButton(text="✅ Оформить", callback_data="checkout")],
                [InlineKeyboardButton(text="📋 К меню", callback_data="back_to_categories")]
            ])
            
            await message.answer(caption, reply_markup=keyboard)
        return
    
    if text.lower() in ["очистить", "очистить корзину", "удалить все"]:
        user_id = message.from_user.id
        
        if user_id in user_cart and user_cart[user_id]:
            item_count = len(user_cart[user_id])
            user_cart[user_id].clear()
            await message.answer(f"✅ Корзина очищена! Удалено {item_count} товаров")
        else:
            await message.answer("🛒 Корзина уже пуста!")
        return
    
    # Поиск товаров
    if len(text) > 2:
        found_items = search_items(text)
        
        if found_items:
            response = "🔍 *Найденные товары:*\n\n"
            for item in found_items[:5]:  # Ограничиваем 5 результатами
                response += f"• {item['name']} - {item['price']}₽\n"
            
            if len(found_items) > 5:
                response += f"\n...и ещё {len(found_items) - 5} товаров\n"
            
            response += "\nИспользуйте кнопки меню для добавления в корзину."
            await message.answer(response)
            return
    
    # Частые вопросы
    faq = {
        "цена": "💰 Цены указаны рядом с каждым товаром в меню.",
        "доставка": "🚚 Доставка занимает 30-60 минут. Бесплатная доставка от 1000₽.",
        "время": "⏰ Мы работаем ежедневно с 10:00 до 23:00.",
        "оплата": "💳 Принимаем наличные и карту при получении.",
        "контакты": "📞 Телефон: +7 (999) 123-45-67\n📍 Адрес: ул. Примерная, д. 1",
        "помощь": "ℹ️ Напишите /menu для просмотра меню или используйте кнопки.",
        "привет": "👋 Привет! Напишите /menu для выбора категории.",
        "спасибо": "😊 Пожалуйста! Приятного аппетита!"
    }
    
    text_lower = text.lower()
    for keyword, answer in faq.items():
        if keyword in text_lower:
            await message.answer(answer)
            return
    
    # Стандартный ответ
    await message.answer(
        "🤖 Используйте кнопки меню или напишите:\n\n"
        "• **/menu** - показать меню\n"
        "• **Название блюда** - поиск по меню\n"
        "• **Корзина** - посмотреть корзину"
    )

async def main():
    """Главная функция запуска бота"""
    logger.info("=" * 50)
    logger.info("ЗАПУСК FOOD EXPRESS БОТА")
    logger.info("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        logger.info("Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())
