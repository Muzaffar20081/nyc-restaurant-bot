import os
import logging
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, CAFES, DEFAULT_CAFE
from ai_brain import ask_grok

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_cart = defaultdict(list)
ai_mode = defaultdict(bool)
user_cafe = defaultdict(lambda: DEFAULT_CAFE)

# МЕНЮ ПРЯМО В КОДЕ - НЕ НУЖНЫ ОТДЕЛЬНЫЕ ФАЙЛЫ
MENUS = {
    "italy": {
        "CATEGORIES": {
            "🍕 Пицца": {
                "Маргарита": 450,
                "Пепперони": 550,
                "Четыре сыра": 500,
                "Гавайская": 520
            },
            "🍝 Паста": {
                "Карбонара": 400,
                "Болоньезе": 450,
                "Альфредо": 420
            },
            "🥗 Салаты": {
                "Цезарь": 350,
                "Греческий": 300,
                "Овощной": 250
            },
            "🍹 Напитки": {
                "Кола": 150,
                "Фанта": 150,
                "Спрайт": 150,
                "Вода": 100
            }
        },
        "MENU_TEXT": "🍕 *Итальянская кухня*\n\nНасладитесь настоящей итальянской кухней! Пицца, паста, салаты и многое другое."
    },
    "sushi": {
        "CATEGORIES": {
            "🍣 Роллы": {
                "Филадельфия": 450,
                "Калифорния": 400,
                "Запеченный ролл": 500,
                "Унаги ролл": 480
            },
            "🍱 Сеты": {
                "Сет на 2 персоны": 1200,
                "Сет на 4 персоны": 2000,
                "Праздничный сет": 2500
            },
            "🍤 Закуски": {
                "Эби-сякэ": 300,
                "Гедза": 250,
                "Эдамаме": 200
            },
            "🍵 Напитки": {
                "Зеленый чай": 150,
                "Рамен": 350,
                "Саке": 400
            }
        },
        "MENU_TEXT": "🍣 *Суши-бар 'Токио'*\n\nПопробуйте лучшие японские блюда! Свежие роллы, сеты и традиционные напитки."
    },
    "burger": {
        "CATEGORIES": {
            "🍔 Бургеры": {
                "Чизбургер": 300,
                "Чикенбургер": 350,
                "Дабл бургер": 450,
                "Вегетарианский": 320
            },
            "🍟 Закуски": {
                "Картофель фри": 150,
                "Наггетсы": 200,
                "Луковые кольца": 180
            },
            "🥤 Напитки": {
                "Кола": 150,
                "Молочный коктейль": 250,
                "Лимонад": 180
            },
            "🍦 Десерты": {
                "Мороженое": 150,
                "Чизкейк": 280,
                "Кексик": 120
            }
        },
        "MENU_TEXT": "🍔 *Бургер-хаус*\n\nСамые сочные бургеры в городе! Только свежие ингредиенты и хрустящая картошка."
    }
}

def load_menu(cafe_key):
    """Загружает меню для конкретного кафе"""
    try:
        logger.info(f"Загрузка меню для кафе: {cafe_key}")
        
        if cafe_key not in CAFES:
            logger.warning(f"Кафе {cafe_key} не найдено, используется {DEFAULT_CAFE}")
            cafe_key = DEFAULT_CAFE
        
        # Получаем меню из словаря
        if cafe_key in MENUS:
            menu_data = MENUS[cafe_key]
            CATEGORIES = menu_data["CATEGORIES"]
            MENU_TEXT = menu_data["MENU_TEXT"]
            
            # Создаем ALL_ITEMS из CATEGORIES
            ALL_ITEMS = {}
            for category_items in CATEGORIES.values():
                ALL_ITEMS.update(category_items)
            
            logger.info(f"Меню {cafe_key} загружено: {len(CATEGORIES)} категорий, {len(ALL_ITEMS)} товаров")
            return CATEGORIES, ALL_ITEMS, MENU_TEXT
        else:
            logger.error(f"Меню для кафе {cafe_key} не найдено в словаре MENUS")
            return {}, {}, "📋 Меню временно недоступно"
            
    except Exception as e:
        logger.error(f"Ошибка загрузки меню для {cafe_key}: {e}")
        return {}, {}, "📋 Меню временно недоступно"

@dp.message(CommandStart())
async def start(message: types.Message):
    """Обработчик команды /start"""
    try:
        user_id = message.from_user.id
        ai_mode[user_id] = False
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍝 Итальянское кафе", callback_data="cafe_italy")],
            [InlineKeyboardButton(text="🍣 Суши-бар", callback_data="cafe_sushi")],
            [InlineKeyboardButton(text="🍔 Бургер-хаус", callback_data="cafe_burger")],
        ])
        
        welcome_text = """
🎊 *ДОБРО ПОЖАЛОВАТЬ В МИР ВКУСА!* 🎊

🌟 *Выберите кухню вашей мечты:*

• 🍝 *Италия* - нежная паста и ароматная пицца
• 🍣 *Япония* - изысканные суши и роллы  
• 🍔 *Америка* - сочные бургеры и хрустящий картофель

🎯 *Готовы к гастрономическому путешествию?*
"""
        
        await message.answer(
            welcome_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        logger.info(f"Пользователь {user_id} запустил бота")
        
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")
        await message.answer("Произошла ошибка при запуске бота. Попробуйте позже.")

@dp.callback_query(lambda c: c.data.startswith("cafe_"))
async def select_cafe(call: types.CallbackQuery):
    """Выбор кафе"""
    try:
        user_id = call.from_user.id
        cafe_key = call.data[5:]  # Убираем "cafe_"
        
        logger.info(f"Пользователь {user_id} выбирает кафе: {cafe_key}")
        
        if cafe_key in CAFES:
            user_cafe[user_id] = cafe_key
            cafe_name = CAFES[cafe_key]["name"]
            cafe_photo = CAFES[cafe_key].get("photo", "")
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📖 Открыть меню", callback_data="menu")],
                [InlineKeyboardButton(text="🛒 Моя корзина", callback_data="cart")],
                [InlineKeyboardButton(text="✨ AI-Помощник", callback_data="chat_mode")],
                [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
            ])
            
            welcome_message = f"""
🏪 *{cafe_name}*

🎉 *Добро пожаловать в мир изысканных вкусов!*

🍽️ *Готовы открыть для себя новые гастрономические горизонты?*

💫 *Выбирайте удобный способ заказа:*
"""
            
            try:
                if cafe_photo and cafe_photo.startswith("http"):
                    await bot.send_photo(
                        chat_id=call.message.chat.id,
                        photo=cafe_photo,
                        caption=welcome_message,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                    await call.message.delete()
                else:
                    await call.message.edit_text(
                        welcome_message,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.warning(f"Не удалось отредактировать сообщение: {e}")
                await call.message.answer(
                    welcome_message,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            
            logger.info(f"Пользователь {user_id} выбрал кафе: {cafe_name}")
        else:
            await call.answer("❌ Кафе не найдено")
            logger.warning(f"Кафе {cafe_key} не найдено для пользователя {user_id}")
        
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в select_cafe: {e}")
        await call.answer("❌ Произошла ошибка при выборе кафе")

@dp.callback_query(lambda c: c.data == "menu")
async def show_categories(call: types.CallbackQuery):
    """Показать категории меню"""
    try:
        user_id = call.from_user.id
        ai_mode[user_id] = False
        
        cafe_key = user_cafe[user_id]
        CATEGORIES, ALL_ITEMS, MENU_TEXT = load_menu(cafe_key)
        cafe_name = CAFES[cafe_key]["name"]
        
        logger.info(f"Показ категорий для {cafe_name}, категорий: {len(CATEGORIES)}")
        
        if not CATEGORIES:
            await call.answer("⚠️ Меню пустое или недоступно")
            error_text = f"""
🏪 *{cafe_name}*

⚠️ *Меню временно недоступно*

Пожалуйста, выберите другое кафе или попробуйте позже.
"""
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")],
                [InlineKeyboardButton(text="🛒 Моя корзина", callback_data="cart")]
            ])
            await call.message.edit_text(
                text=error_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        
        keyboard = []
        for category_name in CATEGORIES.keys():
            # Упрощаем создание callback_data
            clean_name = ''.join([c for c in category_name if not c in ['🍕', '🍝', '🥗', '🍹', '🍣', '🍱', '🍤', '🍵', '🍔', '🍟', '🥤', '🍦']]).strip()
            callback_data = f"category_{clean_name.replace(' ', '_')}"
            keyboard.append([InlineKeyboardButton(
                text=f"🎯 {category_name}", 
                callback_data=callback_data
            )])
        
        keyboard += [
            [InlineKeyboardButton(text="🛒 Посмотреть корзину", callback_data="cart")],
            [InlineKeyboardButton(text="✨ AI-Помощник", callback_data="chat_mode")],
            [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
        ]
        
        await call.message.edit_text(
            text=f"🏪 *{cafe_name}*\n\n{MENU_TEXT}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_categories: {e}")
        await call.answer("❌ Ошибка при загрузке меню")

@dp.callback_query(lambda c: c.data.startswith("category_"))
async def show_category_items(call: types.CallbackQuery):
    """Показать товары в категории"""
    try:
        user_id = call.from_user.id
        ai_mode[user_id] = False
        
        cafe_key = user_cafe[user_id]
        CATEGORIES, ALL_ITEMS, _ = load_menu(cafe_key)
        
        category_key = call.data[9:].replace('_', ' ')
        logger.info(f"Показ товаров категории: {category_key}")
        
        # Ищем полное название категории
        full_category_name = None
        for cat_name in CATEGORIES.keys():
            clean_name = ''.join([c for c in cat_name if not c in ['🍕', '🍝', '🥗', '🍹', '🍣', '🍱', '🍤', '🍵', '🍔', '🍟', '🥤', '🍦']]).strip()
            if clean_name == category_key or cat_name == category_key:
                full_category_name = cat_name
                break
        
        if not full_category_name or full_category_name not in CATEGORIES:
            await call.answer("❌ Категория не найдена")
            return
        
        items = CATEGORIES[full_category_name]
        if not items:
            await call.answer("❌ В этой категории нет товаров")
            return
        
        keyboard = []
        items_list = list(items.items())
        
        # Кнопки товаров
        for i in range(0, len(items_list), 2):
            row = []
            for j in range(2):
                if i + j < len(items_list):
                    item_name, price = items_list[i + j]
                    # Упрощаем callback_data для товаров
                    item_id = item_name[:20].replace(' ', '_')
                    row.append(InlineKeyboardButton(
                        text=f"{item_name}\n💎 {price}₽",
                        callback_data=f"add_{item_id}"
                    ))
            if row:
                keyboard.append(row)
        
        keyboard += [
            [InlineKeyboardButton(text="🔙 Назад к меню", callback_data="menu")],
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
        ]
        
        await call.message.edit_text(
            text=f"🎯 *{full_category_name}*\n\n✨ *Выберите блюдо, которое порадует ваш вкус:*",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_category_items: {e}")
        await call.answer("❌ Ошибка при загрузке товаров")

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(call: types.CallbackQuery):
    """Добавить товар в корзину"""
    try:
        user_id = call.from_user.id
        cafe_key = user_cafe[user_id]
        CATEGORIES, ALL_ITEMS, _ = load_menu(cafe_key)
        
        item_id = call.data[4:]  # Убираем "add_"
        logger.info(f"Добавление товара {item_id} в корзину пользователя {user_id}")
        
        # Ищем товар по ID или имени
        item_name = None
        for name in ALL_ITEMS.keys():
            if name[:20].replace(' ', '_') == item_id or name == item_id:
                item_name = name
                break
        
        if item_name and item_name in ALL_ITEMS:
            user_cart[user_id].append({
                "name": item_name, 
                "price": ALL_ITEMS[item_name],
                "cafe": cafe_key
            })
            await call.answer(f"✅ {item_name}\n🎉 Добавлено в корзину!")
            logger.info(f"Товар {item_name} добавлен в корзину пользователя {user_id}")
        else:
            await call.answer("❌ Товар не найден")
            logger.warning(f"Товар {item_id} не найден для пользователя {user_id}")
            
    except Exception as e:
        logger.error(f"Ошибка в add_to_cart: {e}")
        await call.answer("❌ Ошибка при добавлении в корзину")

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    """Показать корзину"""
    try:
        user_id = call.from_user.id
        ai_mode[user_id] = False
        
        cart_items = user_cart[user_id]
        cafe_key = user_cafe[user_id]
        cafe_name = CAFES[cafe_key]["name"]
        
        logger.info(f"Показ корзины пользователя {user_id}, товаров: {len(cart_items)}")
        
        if not cart_items:
            text = f"""
🏪 *{cafe_name}*

🛒 *ВАША КОРЗИНА ПУСТА* 🛒

💫 *Давайте наполним её вкусняшками!*
🌟 *Выберите что-нибудь из нашего меню*
"""
            keyboard = [
                [InlineKeyboardButton(text="📖 Перейти в меню", callback_data="menu")],
                [InlineKeyboardButton(text="✨ AI-Помощник", callback_data="chat_mode")],
                [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
            ]
        else:
            total = sum(item["price"] for item in cart_items)
            text = f"""
🏪 *{cafe_name}*

🛒 *ВАША КОРЗИНА:* 🛒
"""
            counts = {}
            for item in cart_items:
                name = item["name"]
                counts[name] = counts.get(name, 0) + 1
            
            for name, cnt in counts.items():
                price_per_item = next(item["price"] for item in cart_items if item["name"] == name)
                total_price = price_per_item * cnt
                text += f"├ {name}\n"
                text += f"│   ✕{cnt} = {total_price}₽\n"
            
            text += f"\n💰 *ИТОГО: {total}₽* 💰"
            
            keyboard = [
                [InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")],
                [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
                [InlineKeyboardButton(text="📖 Продолжить покупки", callback_data="menu")],
                [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
            ]
        
        await call.message.edit_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_cart: {e}")
        await call.answer("❌ Ошибка при загрузке корзины")

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(call: types.CallbackQuery):
    """Очистить корзину"""
    try:
        user_id = call.from_user.id
        user_cart[user_id].clear()
        logger.info(f"Корзина очищена для пользователя {user_id}")
        await call.answer("🗑️ Корзина очищена")
        await show_cart(call)
    except Exception as e:
        logger.error(f"Ошибка в clear_cart: {e}")
        await call.answer("❌ Ошибка при очистке корзины")

@dp.callback_query(lambda c: c.data == "checkout")
async def checkout(call: types.CallbackQuery):
    """Оформление заказа"""
    try:
        user_id = call.from_user.id
        cart_items = user_cart[user_id].copy()
        
        if not cart_items:
            await call.answer("❌ Корзина пуста")
            return
        
        cafe_key = user_cafe[user_id]
        cafe_name = CAFES[cafe_key]["name"]
        total = sum(item["price"] for item in cart_items)
        
        logger.info(f"Оформление заказа для пользователя {user_id}, сумма: {total}₽")
        
        order_text = f"""
🎊 *ЗАКАЗ ПРИНЯТ!* 🎊

🏪 *Из:* {cafe_name}

📦 *Ваш заказ:*
"""
        counts = {}
        for item in cart_items:
            name = item["name"]
            counts[name] = counts.get(name, 0) + 1
        
        for name, cnt in counts.items():
            price_per_item = next(item["price"] for item in cart_items if item["name"] == name)
            total_price = price_per_item * cnt
            order_text += f"├ {name}\n"
            order_text += f"│   ✕{cnt} = {total_price}₽\n"
        
        order_text += f"\n💰 *СУММА ЗАКАЗА: {total}₽* 💰\n\n"
        order_text += "⏰ *Менеджер свяжется с вами в ближайшее время!*\n"
        order_text += "📞 *Ожидайте звонка!*"
        
        # Очищаем корзину после оформления
        user_cart[user_id].clear()
        
        await call.message.edit_text(
            text=order_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍽️ Сделать новый заказ", callback_data="menu")]
            ]),
            parse_mode="Markdown"
        )
        await call.answer("🎉 Заказ отправлен!")
        
    except Exception as e:
        logger.error(f"Ошибка в checkout: {e}")
        await call.answer("❌ Ошибка при оформлении заказа")

@dp.callback_query(lambda c: c.data == "chat_mode")
async def enable_chat_mode(call: types.CallbackQuery):
    """Включить AI-помощника"""
    try:
        user_id = call.from_user.id
        ai_mode[user_id] = True
        cafe_key = user_cafe[user_id]
        cafe_name = CAFES[cafe_key]["name"]
        
        await call.message.edit_text(
            f"""
🏪 *{cafe_name}*

✨ *AI-ПОМОЩНИК АКТИВИРОВАН!* ✨

💫 *Теперь просто напишите что хотите:*

• 🍕 "2 пиццы и колу"
• 🛒 "Покажи корзину" 
• 🗑️ "Очисти корзину"
• 💡 "Что посоветуешь?"
• ❓ "Что популярного?"

🎯 *Я всё пойму и помогу сделать заказ!* 🎯
""",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📖 Вернуться в меню", callback_data="menu")],
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
                [InlineKeyboardButton(text="❌ Выключить AI", callback_data="disable_ai")]
            ]),
            parse_mode="Markdown"
        )
        await call.answer("✨ AI-помощник включен!")
        
    except Exception as e:
        logger.error(f"Ошибка в enable_chat_mode: {e}")
        await call.answer("❌ Ошибка при включении AI")

@dp.callback_query(lambda c: c.data == "disable_ai")
async def disable_ai_mode(call: types.CallbackQuery):
    """Выключить AI-помощника"""
    try:
        user_id = call.from_user.id
        ai_mode[user_id] = False
        cafe_key = user_cafe[user_id]
        cafe_name = CAFES[cafe_key]["name"]
        
        await call.message.edit_text(
            f"""
🏪 *{cafe_name}*

🤖 *AI-ПОМОЩНИК ОТКЛЮЧЁН* 🤖

💫 *Используйте кнопки для навигации:* 💫
""",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📖 Меню", callback_data="menu")],
                [InlineKeyboardButton(text="✨ Включить AI", callback_data="chat_mode")],
                [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
            ]),
            parse_mode="Markdown"
        )
        await call.answer("❌ AI выключен")
        
    except Exception as e:
        logger.error(f"Ошибка в disable_ai_mode: {e}")
        await call.answer("❌ Ошибка при выключении AI")

@dp.callback_query(lambda c: c.data == "change_cafe")
async def change_cafe(call: types.CallbackQuery):
    """Сменить кафе"""
    try:
        user_id = call.from_user.id
        user_cart[user_id] = []
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍝 Итальянское кафе", callback_data="cafe_italy")],
            [InlineKeyboardButton(text="🍣 Суши-бар", callback_data="cafe_sushi")],
            [InlineKeyboardButton(text="🍔 Бургер-хаус", callback_data="cafe_burger")],
        ])
        
        await call.message.edit_text(
            "🔄 *СМЕНА КАФЕ*\n\n🗑️ *Корзина очищена!*\n\n🎯 *Выберите новое кафе:*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в change_cafe: {e}")
        await call.answer("❌ Ошибка при смене кафе")

@dp.message()
async def handle_message(message: types.Message):
    """Обработка текстовых сообщений"""
    try:
        user_id = message.from_user.id
        text = message.text.strip()
        
        cafe_key = user_cafe[user_id]
        _, ALL_ITEMS, _ = load_menu(cafe_key)
        
        logger.info(f"Сообщение от пользователя {user_id}: {text}, AI режим: {ai_mode.get(user_id, False)}")
        
        if ai_mode.get(user_id, False):
            cart_items = user_cart[user_id]
            cart_info = "🛒 пустая"
            if cart_items:
                total = sum(item["price"] for item in cart_items)
                counts = {}
                for item in cart_items:
                    counts[item["name"]] = counts.get(item["name"], 0) + 1
                cart_info = "🛒 " + ", ".join(f"{n}×{c}" for n, c in counts.items()) + f" → {total}₽"
            
            response = await ask_grok(text, cart_info, cafe_key, ALL_ITEMS)
            
            await message.answer(
                f"✨ *AI-Помощник:*\n\n{response}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📖 Меню", callback_data="menu")],
                    [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
                    [InlineKeyboardButton(text="❌ Выключить AI", callback_data="disable_ai")]
                ])
            )
        else:
            await message.answer(
                "🤔 *Не понял команду*\n\n💫 *Выберите способ заказа:*",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📖 Меню", callback_data="menu")],
                    [InlineKeyboardButton(text="✨ AI-Помощник", callback_data="chat_mode")],
                    [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
                ])
            )
            
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")

async def main():
    """Основная функция запуска бота"""
    try:
        print("=" * 50)
        print("🎊 БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ! 🍽️")
        print("✨ Красивое меню активировано!")
        print("🤖 AI-помощник готов помочь!")
        print(f"📊 Доступные кафе: {', '.join(CAFES.keys())}")
        print("=" * 50)
        
        logger.info("Бот запущен успешно")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        print(f"❌ Критическая ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
