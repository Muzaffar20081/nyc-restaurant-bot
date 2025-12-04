import os
import importlib
import logging
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from config import BOT_TOKEN, CAFES, DEFAULT_CAFE
from ai_brain import ask_grok

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилища данных пользователей
user_cart = defaultdict(list)
ai_mode = defaultdict(bool)
user_cafe = defaultdict(lambda: DEFAULT_CAFE)
user_states = defaultdict(dict)  # Для хранения состояния пользователя

# Кэш загруженных меню
MENU_CACHE = {}

def load_menu(cafe_key):
    """Загружает меню для конкретного кафе с кэшированием"""
    try:
        if cafe_key not in CAFES:
            cafe_key = DEFAULT_CAFE
            logger.warning(f"Кафе {cafe_key} не найдено, используется DEFAULT_CAFE")
        
        # Проверяем кэш
        if cafe_key in MENU_CACHE:
            return MENU_CACHE[cafe_key]
        
        cafe_config = CAFES[cafe_key]
        module_path = cafe_config["menu_file"]
        
        # Динамический импорт модуля меню
        if module_path.startswith('.'):
            # Относительный импорт
            module_path = module_path.lstrip('.')
            from menus import italian_menu, sushi_menu, burger_menu
            if cafe_key == "italy":
                return italian_menu.CATEGORIES, italian_menu.ALL_ITEMS, italian_menu.MENU_TEXT
            elif cafe_key == "sushi":
                return sushi_menu.CATEGORIES, sushi_menu.ALL_ITEMS, sushi_menu.MENU_TEXT
            elif cafe_key == "burger":
                return burger_menu.CATEGORIES, burger_menu.ALL_ITEMS, burger_menu.MENU_TEXT
        else:
            # Абсолютный импорт
            menu_module = importlib.import_module(module_path)
            result = (menu_module.CATEGORIES, menu_module.ALL_ITEMS, menu_module.MENU_TEXT)
            MENU_CACHE[cafe_key] = result
            return result
            
    except ImportError as e:
        logger.error(f"Ошибка импорта меню для {cafe_key}: {e}")
        # Возвращаем пустое меню
        return {}, {}, "📋 Меню временно недоступно"
    except Exception as e:
        logger.error(f"Ошибка загрузки меню для {cafe_key}: {e}")
        return {}, {}, "📋 Меню временно недоступно"

@dp.message(CommandStart())
async def start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    ai_mode[user_id] = False
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍝 Итальянское кафе", callback_data="cafe:italy")],
        [InlineKeyboardButton(text="🍣 Суши-бар", callback_data="cafe:sushi")],
        [InlineKeyboardButton(text="🍔 Бургер-хаус", callback_data="cafe:burger")],
    ])
    
    welcome_text = """
🎊 *ДОБРО ПОЖАЛОВАТЬ В МИР ВКУСА!* 🎊

🌟 *Выберите кухню вашей мечты:*

• 🍝 *Италия* - нежная паста и ароматная пицца
• 🍣 *Япония* - изысканные суши и роллы  
• 🍔 *Америка* - сочные бургеры и хрустящий картофель

🎯 *Готовы к гастрономическому путешествию?*
"""
    
    try:
        await message.answer(
            welcome_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")

@dp.callback_query(lambda c: c.data.startswith("cafe:"))
async def select_cafe(call: types.CallbackQuery):
    """Выбор кафе"""
    user_id = call.from_user.id
    cafe_key = call.data.split(":")[1]
    
    try:
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
                if cafe_photo:
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
            except TelegramBadRequest:
                # Если сообщение уже отредактировано, отправляем новое
                await call.message.answer(
                    welcome_message,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
        
        await call.answer()
    except Exception as e:
        logger.error(f"Ошибка в select_cafe: {e}")
        await call.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")

@dp.callback_query(lambda c: c.data == "menu")
async def show_categories(call: types.CallbackQuery):
    """Показать категории меню"""
    user_id = call.from_user.id
    ai_mode[user_id] = False
    
    try:
        cafe_key = user_cafe[user_id]
        CATEGORIES, ALL_ITEMS, MENU_TEXT = load_menu(cafe_key)
        cafe_name = CAFES[cafe_key]["name"]
        
        if not CATEGORIES:
            await call.answer("⚠️ Меню временно недоступно")
            return
        
        keyboard = []
        for i, category_name in enumerate(CATEGORIES.keys()):
            # Создаем короткий callback_data с индексом категории
            callback_data = f"cat:{i}"
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
        await call.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")

@dp.callback_query(lambda c: c.data.startswith("cat:"))
async def show_category_items(call: types.CallbackQuery):
    """Показать товары в категории"""
    user_id = call.from_user.id
    ai_mode[user_id] = False
    
    try:
        cafe_key = user_cafe[user_id]
        CATEGORIES, ALL_ITEMS, _ = load_menu(cafe_key)
        
        if not CATEGORIES:
            await call.answer("⚠️ Меню временно недоступно")
            return
        
        category_index = int(call.data.split(":")[1])
        category_keys = list(CATEGORIES.keys())
        
        if category_index >= len(category_keys):
            await call.answer("❌ Категория не найдена")
            return
        
        full_category_name = category_keys[category_index]
        items = CATEGORIES[full_category_name]
        
        if not items:
            await call.answer("❌ В этой категории пока нет товаров")
            return
        
        keyboard = []
        items_list = list(items.items())
        
        # Создаем кнопки товаров
        for i in range(0, len(items_list), 2):
            row = []
            for j in range(2):
                if i + j < len(items_list):
                    item_name, price = items_list[i + j]
                    # Создаем короткий callback_data
                    item_key = f"{category_index}:{i+j}"
                    row.append(InlineKeyboardButton(
                        text=f"{item_name}\n💎 {price}₽",
                        callback_data=f"add:{item_key}"
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
        await call.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")

@dp.callback_query(lambda c: c.data.startswith("add:"))
async def add_to_cart(call: types.CallbackQuery):
    """Добавить товар в корзину"""
    user_id = call.from_user.id
    try:
        cafe_key = user_cafe[user_id]
        CATEGORIES, ALL_ITEMS, _ = load_menu(cafe_key)
        
        if not ALL_ITEMS:
            await call.answer("⚠️ Меню временно недоступно")
            return
        
        # Получаем данные из callback_data
        _, data = call.data.split(":")
        category_index, item_index = map(int, data.split(":"))
        
        # Находим товар
        category_keys = list(CATEGORIES.keys())
        if category_index >= len(category_keys):
            await call.answer("❌ Товар не найден")
            return
        
        category_name = category_keys[category_index]
        category_items = list(CATEGORIES[category_name].items())
        
        if item_index >= len(category_items):
            await call.answer("❌ Товар не найден")
            return
        
        item_name, price = category_items[item_index]
        
        # Добавляем в корзину
        user_cart[user_id].append({
            "name": item_name, 
            "price": price,
            "cafe": cafe_key
        })
        
        await call.answer(f"✅ {item_name}\n🎉 Добавлено в корзину!")
    except Exception as e:
        logger.error(f"Ошибка в add_to_cart: {e}")
        await call.answer("❌ Ошибка при добавлении в корзину")

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    """Показать корзину"""
    user_id = call.from_user.id
    ai_mode[user_id] = False
    
    try:
        cart_items = user_cart[user_id]
        cafe_key = user_cafe[user_id]
        cafe_name = CAFES[cafe_key]["name"]
        
        if not cart_items:
            text = f"""
🏪 *{cafe_name}*

🛒 *ВАША К
