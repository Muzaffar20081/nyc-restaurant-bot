import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from config import BOT_TOKEN, CAFES, DEFAULT_CAFE

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Хранилище данных
user_data = {}

# Меню каждого кафе
MENUS = {
    "italy": {
        "🍕 Пицца": {
            "Маргарита": 450,
            "Пепперони": 550,
            "4 Сыра": 600,
            "Гавайская": 580
        },
        "🍝 Паста": {
            "Карбонара": 380,
            "Болоньезе": 400,
            "Альфредо": 420
        },
        "🥗 Салаты": {
            "Цезарь": 280,
            "Греческий": 300,
            "Оливье": 250
        },
        "🥤 Напитки": {
            "Кола 0.5л": 150,
            "Фанта 0.5л": 150,
            "Вода 0.5л": 100,
            "Сок апельсиновый": 180
        }
    },
    "sushi": {
        "🍣 Классические роллы": {
            "Филадельфия": 300,
            "Калифорния": 280,
            "Унаги": 320,
            "Темпура": 300
        },
        "🍱 Сеты": {
            "Сет на 2 персоны": 1200,
            "Сет на 4 персоны": 2000,
            "Праздничный сет": 2500
        },
        "🍤 Закуски": {
            "Креветки темпура": 350,
            "Эби салата": 280,
            "Гёдза": 220
        },
        "🍵 Напитки": {
            "Зеленый чай": 150,
            "Рамен": 400,
            "Саки": 300
        }
    },
    "burger": {
        "🍔 Бургеры": {
            "Чизбургер": 250,
            "Бургер с беконом": 350,
            "Дабл чизбургер": 450,
            "Вегетарианский": 300
        },
        "🍟 Закуски": {
            "Картофель фри": 150,
            "Наггетсы 6шт": 200,
            "Луковые кольца": 180,
            "Сырные палочки": 220
        },
        "🥤 Напитки": {
            "Кола 0.5л": 150,
            "Молочный коктейль": 250,
            "Лимонад": 180,
            "Кофе": 200
        },
        "🍦 Десерты": {
            "Мороженое": 150,
            "Чизкейк": 200,
            "Кексик": 120
        }
    }
}

# ==================== КЛАВИАТУРЫ ====================

def get_main_keyboard():
    """Основная клавиатура"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍽️ Меню"), KeyboardButton(text="🏪 Кафе")],
            [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="📞 Контакты"), KeyboardButton(text="⭐ Отзывы")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

def get_cafe_keyboard():
    """Клавиатура выбора кафе"""
    buttons = []
    for cafe_key, cafe in CAFES.items():
        buttons.append([InlineKeyboardButton(
            text=f"{cafe['name']}",
            callback_data=f"select_cafe_{cafe_key}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ==================== КОМАНДЫ ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start - начало работы"""
    user_id = message.from_user.id
    
    # Инициализируем данные пользователя
    user_data[user_id] = {
        "cafe": DEFAULT_CAFE,
        "cart": [],
        "total": 0
    }
    
    welcome_text = (
        f"👋 *Добро пожаловать, {message.from_user.first_name}!*\n\n"
        f"Я - бот для заказа еды из различных ресторанов. 🍽️\n\n"
        f"📋 *Доступные функции:*\n"
        f"• 🍽️ Просмотр меню\n"
        f"• 🏪 Выбор ресторана\n"
        f"• 🛒 Корзина заказов\n"
        f"• 📞 Контактная информация\n"
        f"• ⭐ Оставить отзыв\n\n"
        f"📱 *Используйте кнопки ниже или команды:*\n"
        f"/menu - показать меню\n"
        f"/cafe - выбрать кафе\n"
        f"/cart - корзина заказов\n"
        f"/help - помощь\n"
        f"/contacts - контакты\n\n"
        f"🍴 *Сейчас выбрано:* {CAFES[DEFAULT_CAFE]['name']}"
    )
    
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    """Показать меню текущего кафе"""
    await show_menu(message)

@dp.message(Command("cafe"))
async def cmd_cafe(message: types.Message):
    """Выбор кафе"""
    await message.answer("🏪 *Выберите ресторан:*", parse_mode="Markdown", reply_markup=get_cafe_keyboard())

@dp.message(Command("cart"))
async def cmd_cart(message: types.Message):
    """Показать корзину"""
    await show_cart(message)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Помощь"""
    help_text = (
        "❓ *Помощь по использованию бота:*\n\n"
        "📋 *Основные команды:*\n"
        "• /start - начать работу\n"
        "• /menu - показать меню\n"
        "• /cafe - выбрать кафе\n"
        "• /cart - показать корзину\n"
        "• /contacts - контакты\n"
        "• /help - эта справка\n\n"
        "🛒 *Как сделать заказ:*\n"
        "1. Выберите кафе 🏪\n"
        "2. Откройте меню 🍽️\n"
        "3. Добавьте товары в корзину ➕\n"
        "4. Перейдите в корзину 🛒\n"
        "5. Оформите заказ ✅\n\n"
        "📞 *Поддержка:*\n"
        "По всем вопросам обращайтесь в раздел 'Контакты'"
    )
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("contacts"))
async def cmd_contacts(message: types.Message):
    """Контакты"""
    contacts_text = (
        "📞 *Контакты и поддержка:*\n\n"
        "📍 *Адрес офиса:*\n"
        "г. Москва, ул. Примерная, д. 123\n\n"
        "📱 *Телефоны:*\n"
        "• Заказы: +7 (999) 123-45-67\n"
        "• Поддержка: +7 (999) 765-43-21\n\n"
        "⏰ *Часы работы:*\n"
        "Пн-Пт: 9:00 - 22:00\n"
        "Сб-Вс: 10:00 - 23:00\n\n"
        "📧 *Email:*\n"
        "support@restaurant-bot.ru\n\n"
        "💬 *Telegram канал:*\n"
        "@restaurant_bot_news"
    )
    await message.answer(contacts_text, parse_mode="Markdown")

# ==================== ОБРАБОТКА КНОПОК ====================

@dp.message(F.text == "🍽️ Меню")
async def button_menu(message: types.Message):
    await show_menu(message)

@dp.message(F.text == "🏪 Кафе")
async def button_cafe(message: types.Message):
    await cmd_cafe(message)

@dp.message(F.text == "🛒 Корзина")
async def button_cart(message: types.Message):
    await show_cart(message)

@dp.message(F.text == "❓ Помощь")
async def button_help(message: types.Message):
    await cmd_help(message)

@dp.message(F.text == "📞 Контакты")
async def button_contacts(message: types.Message):
    await cmd_contacts(message)

@dp.message(F.text == "⭐ Отзывы")
async def button_reviews(message: types.Message):
    await message.answer(
        "⭐ *Оставить отзыв:*\n\n"
        "Поделитесь вашим мнением о нашем сервисе!\n\n"
        "📝 *Ссылки для отзывов:*\n"
        "• Google Reviews: https://g.page/reviews\n"
        "• Yandex Maps: https://yandex.ru/maps/reviews\n"
        "• 2GIS: https://2gis.ru/reviews\n\n"
        "💬 *Или просто напишите отзыв здесь:*\n"
        "Мы прочитаем и учтем все ваши пожелания!",
        parse_mode="Markdown"
    )

# ==================== ОСНОВНЫЕ ФУНКЦИИ ====================

async def show_menu(message: types.Message):
    """Показать меню выбранного кафе"""
    user_id = message.from_user.id
    cafe_key = user_data.get(user_id, {}).get("cafe", DEFAULT_CAFE)
    cafe_name = CAFES.get(cafe_key, {}).get("name", "Кафе")
    
    if cafe_key not in MENUS:
        await message.answer(f"❌ Меню для {cafe_name} временно недоступно")
        return
    
    menu_text = f"🍽️ *МЕНЮ {cafe_name.upper()}*\n\n"
    
    # Добавляем описание кафе
    cafe_desc = CAFES.get(cafe_key, {}).get("description", "")
    if cafe_desc:
        menu_text += f"_{cafe_desc}_\n\n"
    
    # Добавляем категории и товары
    for category, items in MENUS[cafe_key].items():
        menu_text += f"📁 *{category}:*\n"
        for item_name, price in items.items():
            menu_text += f"├ {item_name} - {price}₽\n"
        menu_text += "\n"
    
    # Создаем кнопки для добавления в корзину
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Кнопки по категориям
    for category, items in MENUS[cafe_key].items():
        row_buttons = []
        for item_name in items.keys():
            callback_data = f"add_{cafe_key}_{item_name.replace(' ', '_')}"
            row_buttons.append(InlineKeyboardButton(
                text=f"➕ {item_name[:15]}",
                callback_data=callback_data
            ))
            if len(row_buttons) >= 2:  # Максимум 2 кнопки в строке
                keyboard.inline_keyboard.append(row_buttons)
                row_buttons = []
        if row_buttons:
            keyboard.inline_keyboard.append(row_buttons)
    
    # Нижние кнопки
    keyboard.inline_keyboard.extend([
        [InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data="view_cart")],
        [InlineKeyboardButton(text="🏪 Сменить ресторан", callback_data="change_cafe")],
        [InlineKeyboardButton(text="🔙 На главную", callback_data="back_to_main")]
    ])
    
    await message.answer(menu_text, parse_mode="Markdown", reply_markup=keyboard)

async def show_cart(message: types.Message):
    """Показать корзину пользователя"""
    user_id = message.from_user.id
    cart_data = user_data.get(user_id, {})
    cart_items = cart_data.get("cart", [])
    
    if not cart_items:
        await message.answer(
            "🛒 *Ваша корзина пуста*\n\n"
            "Добавьте товары из меню, чтобы сделать заказ.",
            parse_mode="Markdown"
        )
        return
    
    cart_text = "🛒 *ВАША КОРЗИНА:*\n\n"
    total = 0
    
    for i, item in enumerate(cart_items, 1):
        cart_text += f"{i}. {item['name']} - {item['price']}₽\n"
        total += item['price']
    
    cart_text += f"\n💰 *ИТОГО: {total}₽*\n"
    cart_text += f"🍴 *Кафе: {CAFES.get(cart_items[0]['cafe'], {}).get('name', 'Неизвестно')}*\n\n"
    cart_text += "Вы можете оформить заказ или изменить корзину:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")],
        [InlineKeyboardButton(text="✏️ Изменить корзину", callback_data="edit_cart")],
        [InlineKeyboardButton(text="🍽️ Вернуться в меню", callback_data="back_to_menu")],
        [InlineKeyboardButton(text="🔙 На главную", callback_data="back_to_main")]
    ])
    
    await message.answer(cart_text, parse_mode="Markdown", reply_markup=keyboard)

# ==================== CALLBACK ОБРАБОТЧИКИ ====================

@dp.callback_query(F.data.startswith("select_cafe_"))
async def select_cafe_callback(call: types.CallbackQuery):
    """Выбор кафе"""
    cafe_key = call.data.replace("select_cafe_", "")
    cafe_info = CAFES.get(cafe_key)
    
    if not cafe_info:
        await call.answer("❌ Кафе не найдено", show_alert=True)
        return
    
    user_id = call.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {}
    
    user_data[user_id]["cafe"] = cafe_key
    
    await call.message.edit_text(
        f"✅ *Вы успешно выбрали:*\n\n"
        f"🏪 *{cafe_info['name']}*\n"
        f"📝 {cafe_info.get('description', '')}\n\n"
        f"Теперь можете открыть меню этого ресторана!",
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart_callback(call: types.CallbackQuery):
    """Добавить товар в корзину"""
    # Формат: add_{cafe_key}_{item_name}
    parts = call.data.split("_")
    if len(parts) < 3:
        await call.answer("❌ Ошибка добавления", show_alert=True)
        return
    
    cafe_key = parts[1]
    item_name_encoded = "_".join(parts[2:])
    item_name = item_name_encoded.replace("_", " ")
    
    # Находим товар и цену
    price = None
    for category, items in MENUS.get(cafe_key, {}).items():
        if item_name in items:
            price = items[item_name]
            break
    
    if not price:
        await call.answer("❌ Товар не найден в меню", show_alert=True)
        return
    
    # Добавляем в корзину
    user_id = call.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"cart": []}
    
    if "cart" not in user_data[user_id]:
        user_data[user_id]["cart"] = []
    
    user_data[user_id]["cart"].append({
        "name": item_name,
        "price": price,
        "cafe": cafe_key
    })
    
    # Подсчитываем общую сумму
    total = sum(item["price"] for item in user_data[user_id]["cart"])
    user_data[user_id]["total"] = total
    
    cafe_name = CAFES.get(cafe_key, {}).get("name", "Ресторан")
    await call.answer(f"✅ {item_name} добавлен в корзину ({cafe_name})")

@dp.callback_query(F.data == "view_cart")
async def view_cart_callback(call: types.CallbackQuery):
    """Показать корзину"""
    await show_cart(call.message)

@dp.callback_query(F.data == "change_cafe")
async def change_cafe_callback(call: types.CallbackQuery):
    """Сменить кафе"""
    await call.message.edit_text("🏪 *Выберите ресторан:*", parse_mode="Markdown", reply_markup=get_cafe_keyboard())

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(call: types.CallbackQuery):
    """Вернуться в меню"""
    await show_menu(call.message)

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_callback(call: types.CallbackQuery):
    """Вернуться на главную"""
    user_id = call.from_user.id
    cafe_key = user_data.get(user_id, {}).get("cafe", DEFAULT_CAFE)
    cafe_name = CAFES.get(cafe_key, {}).get("name", "Кафе")
    
    text = (
        f"🏠 *Главное меню*\n\n"
        f"🍴 *Текущий ресторан:* {cafe_name}\n"
        f"🛒 *Товаров в корзине:* {len(user_data.get(user_id, {}).get('cart', []))}\n\n"
        f"Выберите действие:"
    )
    
    await call.message.edit_text(text, parse_mode="Markdown")
    await call.message.answer("Выберите действие:", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "clear_cart")
async def clear_cart_callback(call: types.CallbackQuery):
    """Очистить корзину"""
    user_id = call.from_user.id
    if user_id in user_data:
        user_data[user_id]["cart"] = []
        user_data[user_id]["total"] = 0
    
    await call.message.edit_text(
        "🗑️ *Корзина успешно очищена!*\n\n"
        "Добавьте новые товары из меню.",
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "edit_cart")
async def edit_cart_callback(call: types.CallbackQuery):
    """Изменить корзину (удалить товары)"""
    user_id = call.from_user.id
    cart_items = user_data.get(user_id, {}).get("cart", [])
    
    if not cart_items:
        await call.answer("❌ Корзина пуста", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for i, item in enumerate(cart_items):
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"❌ {item['name']} - {item['price']}₽",
                callback_data=f"remove_{i}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад в корзину", callback_data="view_cart")
    ])
    
    await call.message.edit_text(
        "✏️ *Удаление товаров из корзины:*\n\n"
        "Нажмите на товар, чтобы удалить его:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("remove_"))
async def remove_item_callback(call: types.CallbackQuery):
    """Удалить товар из корзины"""
    try:
        index = int(call.data.replace("remove_", ""))
        user_id = call.from_user.id
        
        if user_id in user_data and "cart" in user_data[user_id]:
            if 0 <= index < len(user_data[user_id]["cart"]):
                removed_item = user_data[user_id]["cart"].pop(index)
                
                # Пересчитываем сумму
                user_data[user_id]["total"] = sum(
                    item["price"] for item in user_data[user_id]["cart"]
                )
                
                await call.answer(f"❌ {removed_item['name']} удален из корзины")
                await edit_cart_callback(call)  # Обновляем список
                return
    
    except (ValueError, IndexError):
        pass
    
    await call.answer("❌ Ошибка удаления", show_alert=True)

@dp.callback_query(F.data == "checkout")
async def checkout_callback(call: types.CallbackQuery):
    """Оформить заказ"""
    user_id = call.from_user.id
    cart_data = user_data.get(user_id, {})
    cart_items = cart_data.get("cart", [])
    
    if not cart_items:
        await call.answer("❌ Корзина пуста", show_alert=True)
        return
    
    # Собираем информацию о заказе
    total = sum(item["price"] for item in cart_items)
    cafe_key = cart_items[0]["cafe"]
    cafe_name = CAFES.get(cafe_key, {}).get("name", "Неизвестно")
    
    order_text = "✅ *ЗАКАЗ ОФОРМЛЕН!*\n\n"
    order_text += f"📋 *Номер заказа:* #{user_id}_{len(cart_items)}\n"
    order_text += f"🏪 *Ресторан:* {cafe_name}\n"
    order_text += f"👤 *Клиент:* {call.from_user.first_name}\n\n"
    
    order_text += "📦 *Состав заказа:*\n"
    for i, item in enumerate(cart_items, 1):
        order_text += f"{i}. {item['name']} - {item['price']}₽\n"
    
    order_text += f"\n💰 *Сумма заказа:* {total}₽\n"
    order_text += f"📞 *Контакт для связи:* @{call.from_user.username or 'скрыт'}\n\n"
    order_text += "📱 *С вами свяжется оператор для подтверждения заказа и уточнения деталей доставки.*\n\n"
    order_text += "⏱️ *Ориентировочное время доставки:* 30-60 минут\n\n"
    order_text += "🍽️ *Приятного аппетита!*"
    
    # Очищаем корзину после оформления
    user_data[user_id]["cart"] = []
    user_data[user_id]["total"] = 0
    
    await call.message.edit_text(order_text, parse_mode="Markdown")

# ==================== ЗАПУСК БОТА ====================

async def main():
    """Запуск бота"""
    try:
        # Проверяем соединение
        bot_info = await bot.get_me()
        logger.info(f"🤖 Бот запущен: @{bot_info.username}")
        logger.info(f"📝 ID бота: {bot_info.id}")
        logger.info(f"👑 Имя: {bot_info.first_name}")
        
        print("=" * 50)
        print("✅ БОТ УСПЕШНО ЗАПУЩЕН!")
        print(f"🤖 Имя: @{bot_info.username}")
        print(f"🆔 ID: {bot_info.id}")
        print("=" * 50)
        print("📱 Перейдите в Telegram и найдите бота")
        print("💬 Начните с команды /start")
        print("=" * 50)
        
        # Запускаем опрос
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        print("\n" + "!" * 50)
        print("❌ ОШИБКА ЗАПУСКА БОТА!")
        print("=" * 50)
        print("Возможные причины:")
        print("1. Неверный токен бота в config.py")
        print("2. Нет интернет-соединения")
        print("3. Библиотека aiogram не установлена")
        print("\nРешение:")
        print("1. Проверьте BOT_TOKEN в config.py")
        print("2. Установите aiogram: pip install aiogram")
        print("3. Проверьте интернет-соединение")
        print("!" * 50)

if __name__ == "__main__":
    asyncio.run(main())
