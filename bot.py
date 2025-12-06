import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

# Импортируем наши модули
from config import BOT_TOKEN, ADMIN_IDS, CAFES
from admin_panel import (
    show_admin_panel, 
    admin_view_menu,
    admin_add_item_step1,
    admin_edit_price_step1,
    admin_delete_item_step1,
    admin_back,
    admin_add_item_step3,
    admin_add_item_step4,
    admin_create_new_category,
    admin_edit_price_final,
    AdminStates
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Проверка админа
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ============ ОСНОВНЫЕ КОМАНДЫ ============

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start"""
    if is_admin(message.from_user.id):
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="👤 Меню пользователя", callback_data="user_menu")],
            [types.InlineKeyboardButton(text="🔧 Админ-панель", callback_data="admin_panel")]
        ])
        text = "👋 Добро пожаловать!\n\nВы администратор. Выберите режим:"
    else:
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🍽️ Меню", callback_data="show_menu")],
            [types.InlineKeyboardButton(text="🤖 AI-помощник", callback_data="ai_helper")],
            [types.InlineKeyboardButton(text="🏪 Сменить кафе", callback_data="change_cafe")]
        ])
        text = "👋 Добро пожаловать в наш ресторан!\n\nВыберите действие:"
    
    await message.answer(text, reply_markup=keyboard)

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Команда /admin - только для админов"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели")
        return
    
    await show_admin_panel(message, CAFES)

# ============ АДМИН ПАНЕЛЬ CALLBACKS ============

@dp.callback_query(lambda call: call.data.startswith("admin_"))
async def handle_admin_callbacks(call: types.CallbackQuery, state: FSMContext):
    """Обработка всех callback от админ-панели"""
    user_id = call.from_user.id
    if not is_admin(user_id):
        await call.answer("❌ Нет доступа", show_alert=True)
        return
    
    # Получаем данные из call.data
    data = call.data
    
    if data == "admin_panel":
        await show_admin_panel(call.message, CAFES)
    
    elif data == "admin_view_menu":
        await admin_view_menu(call, CAFES)
    
    elif data == "admin_add_item":
        await admin_add_item_step1(call, CAFES, state)
    
    elif data == "admin_edit_price":
        await admin_edit_price_step1(call, CAFES)
    
    elif data == "admin_delete_item":
        await admin_delete_item_step1(call, CAFES)
    
    elif data == "admin_back":
        await admin_back(call, CAFES)
    
    elif data == "admin_add_category":
        # Простая команда для добавления категории
        from admin_panel import admin_add_category
        await admin_add_category(call.message, CAFES)
    
    elif data.startswith("add_to_"):
        await admin_add_item_step2(call, state)
    
    elif data.startswith("cat_"):
        await admin_add_item_final(call, state)
    
    elif data == "new_category":
        await call.message.answer("📝 Введите название новой категории:")
        # Состояние уже установлено в admin_add_item_step4
    
    elif data.startswith("edit_price_"):
        await admin_edit_price_step2(call, state)
    
    elif data.startswith("delete_"):
        await admin_delete_item_step2(call)
    
    elif data.startswith("confirm_delete_"):
        await admin_delete_item_final(call)
    
    else:
        await call.answer("❌ Неизвестная команда", show_alert=True)

# ============ FSM ХЕНДЛЕРЫ ДЛЯ АДМИНКИ ============

@dp.message(AdminStates.waiting_for_item_name)
async def handle_item_name(message: types.Message, state: FSMContext):
    """Обработка названия товара"""
    await admin_add_item_step3(message, state)

@dp.message(AdminStates.waiting_for_item_price)
async def handle_item_price(message: types.Message, state: FSMContext):
    """Обработка цены товара"""
    await admin_add_item_step4(message, state, CAFES)

@dp.message(AdminStates.waiting_for_new_price)
async def handle_new_price(message: types.Message, state: FSMContext):
    """Обработка новой цены"""
    await admin_edit_price_final(message, state)

@dp.message(AdminStates.waiting_for_category)
async def handle_new_category(message: types.Message, state: FSMContext):
    """Обработка новой категории"""
    await admin_create_new_category(message, state)

# ============ ПОЛЬЗОВАТЕЛЬСКИЙ ИНТЕРФЕЙС ============

@dp.callback_query(lambda call: call.data == "show_menu")
async def show_user_menu(call: types.CallbackQuery):
    """Показать меню пользователю"""
    from admin_panel import load_menus
    
    menus = load_menus()
    cafe_key = "italy"  # Можно сделать выбор кафе
    
    if cafe_key not in menus or not menus[cafe_key]["CATEGORIES"]:
        await call.message.edit_text("📭 Меню пока пустое. Зайдите позже!")
        return
    
    cafe_name = CAFES.get(cafe_key, {}).get("name", "Кафе")
    text = f"🍽️ *Меню {cafe_name}:*\n\n"
    
    for cat_name, items in menus[cafe_key]["CATEGORIES"].items():
        text += f"📁 *{cat_name}:*\n"
        for item_name, price in items.items():
            text += f"   ├ {item_name} - {price}₽\n"
        text += "\n"
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data="add_to_cart_ask")],
        [types.InlineKeyboardButton(text="🏪 Сменить кафе", callback_data="change_cafe")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="user_menu")]
    ])
    
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query(lambda call: call.data == "ai_helper")
async def show_ai_helper(call: types.CallbackQuery):
    """AI-помощник"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="❓ Что посоветуете?", callback_data="ai_recommend")],
        [types.InlineKeyboardButton(text="🍽️ Составить заказ", callback_data="ai_order")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="user_menu")]
    ])
    
    await call.message.edit_text(
        "🤖 *AI-Помощник*\n\nЧем могу помочь?",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query(lambda call: call.data == "change_cafe")
async def change_cafe(call: types.CallbackQuery):
    """Смена кафе"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=cafe["name"], callback_data=f"select_cafe_{cafe_key}")]
        for cafe_key, cafe in CAFES.items()
    ] + [[types.InlineKeyboardButton(text="🔙 Назад", callback_data="user_menu")]]
    )
    
    await call.message.edit_text(
        "🏪 *Выберите кафе:*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query(lambda call: call.data.startswith("select_cafe_"))
async def select_cafe(call: types.CallbackQuery):
    """Выбор кафе"""
    cafe_key = call.data.replace("select_cafe_", "")
    cafe_name = CAFES.get(cafe_key, {}).get("name", "Кафе")
    
    await call.message.edit_text(
        f"✅ Выбрано: {cafe_name}\n\nТеперь можете посмотреть меню.",
        parse_mode="Markdown"
    )
    # Здесь можно сохранить выбор кафе в состояние пользователя

@dp.callback_query(lambda call: call.data == "user_menu")
async def user_menu(call: types.CallbackQuery):
    """Главное меню пользователя"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🍽️ Меню", callback_data="show_menu")],
        [types.InlineKeyboardButton(text="🤖 AI-помощник", callback_data="ai_helper")],
        [types.InlineKeyboardButton(text="🏪 Сменить кафе", callback_data="change_cafe")]
    ])
    
    await call.message.edit_text(
        "👤 *Меню пользователя*\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ============ ЗАПУСК БОТА ============

async def main():
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
