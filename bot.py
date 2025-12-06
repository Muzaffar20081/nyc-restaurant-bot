import asyncio
import logging
import datetime
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup

# Импортируем наши модули
from config import BOT_TOKEN, ADMIN_IDS, CAFES, DEFAULT_CAFE

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())

# Файл для хранения меню
MENU_FILE = "menus.json"

def load_menus():
    """Загружает меню из файла"""
    try:
        with open(MENU_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Создаем структуру по умолчанию
        default_menus = {}
        for cafe_key in ["italy", "sushi", "burger"]:
            default_menus[cafe_key] = {
                "CATEGORIES": {
                    "🍽️ Основное": {},
                    "🥤 Напитки": {}
                },
                "MENU_TEXT": ""
            }
        save_menus(default_menus)
        return default_menus

def save_menus(menus):
    """Сохраняет меню в файл"""
    try:
        with open(MENU_FILE, 'w', encoding='utf-8') as f:
            json.dump(menus, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения меню: {e}")

# Состояния для админ-панели
class AdminStates(StatesGroup):
    waiting_for_cafe = State()
    waiting_for_category = State()
    waiting_for_item_name = State()
    waiting_for_item_price = State()
    waiting_for_new_price = State()
    waiting_for_new_category = State()

# Хранилище состояний пользователей
user_states = {}

# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

def get_current_time():
    """Получить текущее время в формате HH:MM"""
    now = datetime.datetime.now()
    return now.strftime("%H:%M")

def create_user_keyboard(is_admin_user=False):
    """Создание клавиатуры для пользователя"""
    if is_admin_user:
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="🍽️ Меню")],
                [types.KeyboardButton(text="🤖 AI-помощник")],
                [types.KeyboardButton(text="🏪 Сменить кафе")],
                [types.KeyboardButton(text="🔧 Админ-панель")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    else:
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="🍽️ Меню")],
                [types.KeyboardButton(text="🤖 AI-помощник")],
                [types.KeyboardButton(text="🏪 Сменить кафе")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    return keyboard

async def show_admin_panel(message: types.Message, cafes_config):
    """Показать админ-панель"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📊 Просмотреть меню", callback_data="admin_view_menu")],
        [types.InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_item")],
        [types.InlineKeyboardButton(text="✏️ Изменить цену", callback_data="admin_edit_price")],
        [types.InlineKeyboardButton(text="🗑️ Удалить товар", callback_data="admin_delete_item")],
        [types.InlineKeyboardButton(text="📁 Добавить категорию", callback_data="admin_add_category")],
        [types.InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
    ])
    
    await message.answer(
        "🔧 *Админ-панель управления меню*\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def admin_back(call: types.CallbackQuery):
    """Вернуться в админ-панель"""
    await show_admin_panel(call.message, CAFES)

# ============ КОМАНДЫ БОТА ============

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    # Сохраняем выбранное кафе по умолчанию
    user_states[user_id] = {"cafe": DEFAULT_CAFE}
    
    welcome_text = (
        f"👋 Привет, {first_name}!\n\n"
        f"Добро пожаловать в наш ресторан! 🍽️\n\n"
        f"Я помогу вам:\n"
        f"• 📋 Посмотреть меню\n"
        f"• 🤖 Получить рекомендации\n"
        f"• 🏪 Выбрать кафе\n"
        f"• 🛒 Сделать заказ\n\n"
        f"*Выберите действие снизу или напишите команду:*"
    )
    
    keyboard = create_user_keyboard(is_admin(user_id))
    
    await message.answer(
        welcome_text,
        reply_markup=keyboard
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Команда /help"""
    help_text = (
        "🆘 *Помощь по боту:*\n\n"
        "📋 *Основные команды:*\n"
        "• /start - начать работу с ботом\n"
        "• /menu - показать меню текущего кафе\n"
        "• /cafe - выбрать кафе\n"
        "• /admin - панель управления (только для админов)\n"
        "• /myid - узнать свой ID\n\n"
        "📱 *Быстрые действия (кнопки снизу):*\n"
        "• 🍽️ Меню - посмотреть меню\n"
        "• 🤖 AI-помощник - получить рекомендации\n"
        "• 🏪 Сменить кафе - выбрать другое кафе\n"
        "• 🔧 Админ-панель - управление меню\n\n"
        "*Также вы можете просто писать текстом:*\n"
        "• 'меню' - показать меню\n"
        "• 'помощник' - AI-помощник\n"
        "• 'кафе' - сменить кафе\n"
        "• 'админ' - админ-панель"
    )
    
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    """Команда /menu - показать меню"""
    await show_user_menu(message)

@dp.message(Command("cafe"))
async def cmd_cafe(message: types.Message):
    """Команда /cafe - выбрать кафе"""
    await change_cafe_keyboard(message)

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Команда /admin - админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer(
            "❌ *Доступ запрещен!*\n\n"
            "У вас нет прав для доступа к админ-панели.",
            parse_mode="Markdown"
        )
        return
    
    await show_admin_panel(message, CAFES)

@dp.message(Command("myid"))
async def cmd_myid(message: types.Message):
    """Команда /myid - узнать свой ID"""
    user_id = message.from_user.id
    username = message.from_user.username or "не установлен"
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    
    admin_status = "✅ Администратор" if is_admin(user_id) else "👤 Пользователь"
    
    await message.answer(
        f"📋 *Ваши данные:*\n\n"
        f"🆔 *ID:* `{user_id}`\n"
        f"👤 *Имя:* {first_name} {last_name}\n"
        f"📛 *Username:* @{username}\n"
        f"👑 *Статус:* {admin_status}\n\n"
        f"*Текущее время:* {get_current_time()}",
        parse_mode="Markdown"
    )

# ============ ТЕКСТОВЫЕ КОМАНДЫ (кнопки и текст) ============

@dp.message(F.text.lower().in_(["меню", "menu", "🍽️ меню"]))
async def text_menu(message: types.Message):
    """Текстовая команда 'меню'"""
    await show_user_menu(message)

@dp.message(F.text.lower().in_(["ai-помощник", "ai помощник", "помощник", "🤖 ai-помощник", "бот", "помоги"]))
async def text_ai_helper(message: types.Message):
    """Текстовая команда 'ai-помощник'"""
    await show_ai_helper(message)

@dp.message(F.text.lower().in_(["сменить кафе", "кафе", "🏪 сменить кафе", "ресторан", "заведение"]))
async def text_change_cafe(message: types.Message):
    """Текстовая команда 'сменить кафе'"""
    await change_cafe_keyboard(message)

@dp.message(F.text.lower().in_(["админ", "admin", "🔧 админ-панель", "админка", "управление"]))
async def text_admin(message: types.Message):
    """Текстовая команда 'админ'"""
    if not is_admin(message.from_user.id):
        await message.answer(
            "❌ *Доступ запрещен!*\n\n"
            "У вас нет прав для доступа к админ-панели.",
            parse_mode="Markdown"
        )
        return
    
    await show_admin_panel(message, CAFES)

# ============ ОСНОВНЫЕ ФУНКЦИИ ============

async def show_user_menu(message: types.Message):
    """Показать меню пользователю"""
    user_id = message.from_user.id
    
    # Получаем выбранное кафе пользователя
    cafe_key = user_states.get(user_id, {}).get("cafe", DEFAULT_CAFE)
    cafe_name = CAFES.get(cafe_key, {}).get("name", cafe_key)
    
    menus = load_menus()
    
    if cafe_key not in menus or not menus[cafe_key]["CATEGORIES"]:
        await message.answer(
            f"📭 *Меню кафе '{cafe_name}' пока пустое.*\n\n"
            f"Администратор скоро добавит товары.",
            parse_mode="Markdown"
        )
        return
    
    text = f"🍽️ *Меню {cafe_name}:*\n\n"
    
    for cat_name, items in menus[cafe_key]["CATEGORIES"].items():
        text += f"📁 *{cat_name}:*\n"
        if not items:
            text += "   └ (пусто)\n"
        else:
            for item_name, price in items.items():
                text += f"   ├ {item_name} - {price}₽\n"
        text += "\n"
    
    # Обрезаем если слишком длинное
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (меню продолжается)"
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data="cart_info")],
        [types.InlineKeyboardButton(text="🏪 Сменить кафе", callback_data="change_cafe_main")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

async def show_ai_helper(message: types.Message):
    """Показать AI-помощника"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="❓ Что посоветуете?", callback_data="ai_recommend")],
        [types.InlineKeyboardButton(text="🍽️ Составить заказ", callback_data="ai_order")],
        [types.InlineKeyboardButton(text="📞 Связаться с поддержкой", callback_data="ai_support")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    
    await message.answer(
        "🤖 *AI-Помощник*\n\n"
        "Я помогу вам с выбором блюд, составлением заказа "
        "или отвечу на вопросы о нашем ресторане!\n\n"
        "Чем могу помочь?",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def change_cafe_keyboard(message: types.Message):
    """Показать клавиатуру для смены кафе"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=cafe["name"], callback_data=f"select_cafe_{cafe_key}")]
        for cafe_key, cafe in CAFES.items()
    ] + [[types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
    )
    
    await message.answer(
        "🏪 *Выберите кафе:*\n\n"
        "Все заказы будут относиться к выбранному кафе.",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ============ CALLBACK ОБРАБОТЧИКИ ============

@dp.callback_query(lambda call: call.data == "back_to_main")
async def back_to_main_menu(call: types.CallbackQuery):
    """Вернуться в главное меню"""
    user_id = call.from_user.id
    keyboard = create_user_keyboard(is_admin(user_id))
    
    await call.message.edit_text(
        "🏠 *Главное меню*\n\nВыберите действие:",
        parse_mode="Markdown"
    )
    await call.message.answer("Выберите действие:", reply_markup=keyboard)

@dp.callback_query(lambda call: call.data == "change_cafe_main")
async def change_cafe_callback(call: types.CallbackQuery):
    """Смена кафе из меню"""
    await change_cafe_keyboard(call.message)

@dp.callback_query(lambda call: call.data.startswith("select_cafe_"))
async def select_cafe_callback(call: types.CallbackQuery):
    """Выбор кафе"""
    cafe_key = call.data.replace("select_cafe_", "")
    cafe_name = CAFES.get(cafe_key, {}).get("name", cafe_key)
    
    user_id = call.from_user.id
    user_states[user_id] = {"cafe": cafe_key}
    
    await call.message.edit_text(
        f"✅ *Выбрано: {cafe_name}*\n\n"
        f"Теперь можете посмотреть меню этого кафе.",
        parse_mode="Markdown"
    )

@dp.callback_query(lambda call: call.data == "cart_info")
async def cart_info(call: types.CallbackQuery):
    """Информация о корзине"""
    await call.message.edit_text(
        "🛒 *Корзина*\n\n"
        "Функция корзины скоро будет добавлена!\n"
        "Пока вы можете делать заказы через AI-помощника.",
        parse_mode="Markdown"
    )

# ============ АДМИН CALLBACK ОБРАБОТЧИКИ ============

@dp.callback_query(lambda call: call.data == "admin_view_menu")
async def admin_view_menu_callback(call: types.CallbackQuery):
    """Админ: просмотр меню"""
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа", show_alert=True)
        return
    
    menus = load_menus()
    
    if not menus:
        await call.message.edit_text("📭 Меню пустое. Добавьте товары!")
        return
    
    text = "📋 *ТЕКУЩЕЕ МЕНЮ:*\n\n"
    
    for cafe_key, cafe_data in menus.items():
        cafe_name = CAFES.get(cafe_key, {}).get("name", cafe_key)
        text += f"🏪 *{cafe_name}:*\n"
        
        categories = cafe_data.get("CATEGORIES", {})
        if not categories:
            text += "   └ (пусто)\n"
        else:
            for cat_name, items in categories.items():
                text += f"\n   📁 *{cat_name}:*\n"
                if not items:
                    text += "      └ (пусто)\n"
                else:
                    for item_name, price in items.items():
                        text += f"      ├ {item_name} - {price}₽\n"
        text += "\n"
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Назад в админку", callback_data="admin_back")]
    ])
    
    await call.message.edit_text(text[:4000], parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query(lambda call: call.data == "admin_add_item")
async def admin_add_item_callback(call: types.CallbackQuery, state: FSMContext):
    """Админ: начать добавление товара"""
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа", show_alert=True)
        return
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=cafe["name"], callback_data=f"add_to_{cafe_key}")]
        for cafe_key, cafe in CAFES.items()
    ] + [[types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]
    )
    
    await call.message.edit_text(
        "🏪 *Выберите кафе для добавления товара:*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query(lambda call: call.data.startswith("add_to_"))
async def admin_add_item_step2_callback(call: types.CallbackQuery, state: FSMContext):
    """Админ: шаг 2 добавления товара"""
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа", show_alert=True)
        return
    
    cafe_key = call.data.replace("add_to_", "")
    await state.update_data(cafe_key=cafe_key)
    await state.set_state(AdminStates.waiting_for_item_name)
    
    await call.message.edit_text(
        "📝 *Введите название товара:*\n\nПример: `Пицца Пепперони`",
        parse_mode="Markdown"
    )

@dp.message(AdminStates.waiting_for_item_name)
async def admin_add_item_step3_handler(message: types.Message, state: FSMContext):
    """Админ: шаг 3 - обработка названия товара"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return
    
    item_name = message.text.strip()
    if not item_name:
        await message.answer("❌ Название не может быть пустым!")
        return
    
    if len(item_name) > 100:
        await message.answer("❌ Название слишком длинное (макс. 100 символов)!")
        return
    
    await state.update_data(item_name=item_name)
    await state.set_state(AdminStates.waiting_for_item_price)
    
    await message.answer(
        "💰 *Введите цену товара:*\n\nПример: `550`",
        parse_mode="Markdown"
    )

@dp.message(AdminStates.waiting_for_item_price)
async def admin_add_item_step4_handler(message: types.Message, state: FSMContext):
    """Админ: шаг 4 - обработка цены"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return
    
    try:
        price = int(message.text.strip())
        if price <= 0:
            await message.answer("❌ Цена должна быть больше 0!")
            return
        if price > 100000:
            await message.answer("❌ Цена слишком большая!")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    cafe_key = data.get("cafe_key")
    item_name = data.get("item_name")
    
    menus = load_menus()
    if cafe_key not in menus:
        menus[cafe_key] = {"CATEGORIES": {}, "MENU_TEXT": ""}
    
    categories = menus[cafe_key]["CATEGORIES"]
    
    if not categories:
        categories["🍽️ Основное"] = {}
    
    # Показываем категории для выбора
    keyboard_buttons = []
    for cat_name in categories.keys():
        callback_data = f"cat_select:{cafe_key}:{cat_name}"
        keyboard_buttons.append([types.InlineKeyboardButton(
            text=cat_name, 
            callback_data=callback_data
        )])
    
    keyboard_buttons.append([types.InlineKeyboardButton(
        text="➕ Новая категория", 
        callback_data="new_category_for_item"
    )])
    
    keyboard_buttons.append([types.InlineKeyboardButton(
        text="🔙 Отмена", 
        callback_data="admin_back"
    )])
    
    await state.update_data(price=price)
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    cafe_name = CAFES.get(cafe_key, {}).get("name", cafe_key)
    
    await message.answer(
        f"📁 *Выберите категорию для товара:*\n\n"
        f"🏪 Кафе: {cafe_name}\n"
        f"📝 Товар: {item_name}\n"
        f"💰 Цена: {price}₽",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query(lambda call: call.data.startswith("cat_select:"))
async def admin_add_item_final_callback(call: types.CallbackQuery, state: FSMContext):
    """Админ: финальное сохранение товара"""
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа", show_alert=True)
        return
    
    # Формат: cat_select:{cafe_key}:{category_name}
    parts = call.data.split(':')
    if len(parts) < 3:
        await call.answer("❌ Ошибка данных", show_alert=True)
        return
    
    cafe_key = parts[1]
    category_name = ':'.join(parts[2:])
    
    data = await state.get_data()
    item_name = data.get("item_name")
    price = data.get("price")
    
    if not item_name or not price:
        await call.answer("❌ Данные не найдены", show_alert=True)
        return
    
    menus = load_menus()
    
    if cafe_key not in menus:
        menus[cafe_key] = {"CATEGORIES": {}, "MENU_TEXT": ""}
    
    if category_name not in menus[cafe_key]["CATEGORIES"]:
        menus[cafe_key]["CATEGORIES"][category_name] = {}
    
    menus[cafe_key]["CATEGORIES"][category_name][item_name] = price
    save_menus(menus)
    
    await state.clear()
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ Добавить еще", callback_data="admin_add_item")],
        [types.InlineKeyboardButton(text="🔙 В админку", callback_data="admin_back")]
    ])
    
    await call.message.edit_text(
        f"✅ *Товар добавлен!*\n\n"
        f"🏪 Кафе: {CAFES.get(cafe_key, {}).get('name', cafe_key)}\n"
        f"📁 Категория: {category_name}\n"
        f"📝 Товар: {item_name}\n"
        f"💰 Цена: {price}₽",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query(lambda call: call.data == "new_category_for_item")
async def admin_create_new_category_callback(call: types.CallbackQuery, state: FSMContext):
    """Админ: создание новой категории для товара"""
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_for_new_category)
    
    data = await state.get_data()
    item_name = data.get("item_name", "")
    price = data.get("price", 0)
    
    await call.message.edit_text(
        f"📝 *Создание новой категории*\n\n"
        f"Товар: {item_name}\n"
        f"Цена: {price}₽\n\n"
        f"*Введите название новой категории:*\n"
        f"Пример: `🍕 Пицца` или `🥤 Напитки`",
        parse_mode="Markdown"
    )

@dp.message(AdminStates.waiting_for_new_category)
async def admin_save_new_category_handler(message: types.Message, state: FSMContext):
    """Админ: сохранение новой категории с товаром"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа")
        return
    
    category_name = message.text.strip()
    if not category_name:
        await message.answer("❌ Название категории не может быть пустым!")
        return
    
    data = await state.get_data()
    cafe_key = data.get("cafe_key")
    item_name = data.get("item_name")
    price = data.get("price")
    
    if not cafe_key or not item_name or not price:
        await message.answer("❌ Данные не найдены!")
        return
    
    menus = load_menus()
    
    if cafe_key not in menus:
        menus[cafe_key] = {"CATEGORIES": {}, "MENU_TEXT": ""}
    
    menus[cafe_key]["CATEGORIES"][category_name] = {item_name: price}
    save_menus(menus)
    
    await state.clear()
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ Добавить еще", callback_data="admin_add_item")],
        [types.InlineKeyboardButton(text="🔙 В админку", callback_data="admin_back")]
    ])
    
    await message.answer(
        f"✅ *Товар добавлен в новую категорию!*\n\n"
        f"🏪 Кафе: {CAFES.get(cafe_key, {}).get('name', cafe_key)}\n"
        f"📁 Новая категория: {category_name}\n"
        f"📝 Товар: {item_name}\n"
        f"💰 Цена: {price}₽",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query(lambda call: call.data == "admin_edit_price")
async def admin_edit_price_callback(call: types.CallbackQuery):
    """Админ: изменение цены"""
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа", show_alert=True)
        return
    
    await call.message.edit_text(
        "✏️ *Изменение цены*\n\n"
        "Эта функция скоро будет добавлена!\n"
        "Пока используйте удаление и добавление товара заново.",
        parse_mode="Markdown"
    )

@dp.callback_query(lambda call: call.data == "admin_delete_item")
async def admin_delete_item_callback(call: types.CallbackQuery):
    """Админ: удаление товара"""
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа", show_alert=True)
        return
    
    await call.message.edit_text(
        "🗑️ *Удаление товара*\n\n"
        "Эта функция скоро будет добавлена!\n"
        "Пока редактируйте меню вручную через файл menus.json.",
        parse_mode="Markdown"
    )

@dp.callback_query(lambda call: call.data == "admin_add_category")
async def admin_add_category_callback(call: types.CallbackQuery):
    """Админ: добавление категории"""
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа", show_alert=True)
        return
    
    await call.message.edit_text(
        "📁 *Добавление категории*\n\n"
        "Эта функция скоро будет добавлена!\n"
        "Пока создавайте категории при добавлении товара.",
        parse_mode="Markdown"
    )

@dp.callback_query(lambda call: call.data == "admin_back")
async def admin_back_callback(call: types.CallbackQuery):
    """Админ: назад в админ-панель"""
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа", show_alert=True)
        return
    
    await admin_back(call)

# ============ ЗАПУСК БОТА ============

async def main():
    """Запуск бота"""
    try:
        logger.info("=" * 50)
        logger.info("ЗАПУСК БОТА...")
        logger.info(f"Админы: {ADMIN_IDS}")
        logger.info(f"Кафе: {list(CAFES.keys())}")
        logger.info("=" * 50)
        
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
