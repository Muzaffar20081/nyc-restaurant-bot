import asyncio
import logging
import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove

# Импортируем наши модули
from config import BOT_TOKEN, ADMIN_IDS, CAFES, DEFAULT_CAFE
from admin_panel import (
    show_admin_panel, 
    admin_view_menu,
    admin_add_item_step1,
    admin_add_item_step2,
    admin_add_item_step3,
    admin_add_item_step4,
    admin_add_item_final,
    admin_create_new_category_for_item,
    admin_save_new_category_with_item,
    admin_edit_price_step1,
    admin_edit_price_step2,
    admin_edit_price_final,
    admin_delete_item_step1,
    admin_delete_item_step2,
    admin_delete_item_final,
    admin_add_category,
    admin_add_category_step2,
    admin_save_new_category,
    admin_back,
    AdminStates,
    load_menus
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())

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
