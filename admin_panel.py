import json
import logging
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)

# Состояния для админ-панели
class AdminStates(StatesGroup):
    waiting_for_cafe = State()
    waiting_for_category = State()
    waiting_for_item_name = State()
    waiting_for_item_price = State()
    waiting_for_new_price = State()
    waiting_for_item_to_delete = State()

# Файл для хранения меню
MENU_FILE = "menus.json"

def load_menus():
    """Загружает меню из файла"""
    try:
        with open(MENU_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_menus(menus):
    """Сохраняет меню в файл"""
    with open(MENU_FILE, 'w', encoding='utf-8') as f:
        json.dump(menus, f, ensure_ascii=False, indent=2)

# ============ АДМИН КОМАНДЫ ============

async def show_admin_panel(message: types.Message, cafes_config):
    """Показать админ-панель"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📊 Просмотреть меню", callback_data="admin_view_menu")],
        [types.InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_item")],
        [types.InlineKeyboardButton(text="✏️ Изменить цену", callback_data="admin_edit_price")],
        [types.InlineKeyboardButton(text="🗑️ Удалить товар", callback_data="admin_delete_item")],
        [types.InlineKeyboardButton(text="📁 Добавить категорию", callback_data="admin_add_category")],
    ])
    
    await message.answer(
        "🔧 *Админ-панель управления меню*\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ============ ПРОСМОТР МЕНЮ ============

async def admin_view_menu(call: types.CallbackQuery, cafes_config):
    """Показать все меню"""
    menus = load_menus()
    
    if not menus:
        await call.message.edit_text("📭 Меню пустое. Добавьте товары!")
        return
    
    text = "📋 *ТЕКУЩЕЕ МЕНЮ:*\n\n"
    
    for cafe_key, cafe_data in menus.items():
        cafe_name = cafes_config.get(cafe_key, {}).get("name", cafe_key)
        text += f"🏪 *{cafe_name}:*\n"
        
        categories = cafe_data.get("CATEGORIES", {})
        for cat_name, items in categories.items():
            text += f"\n📁 *{cat_name}:*\n"
            for item_name, price in items.items():
                text += f"   ├ {item_name} - {price}₽\n"
        text += "\n"
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    
    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

# ============ ДОБАВЛЕНИЕ ТОВАРА ============

async def admin_add_item_step1(call: types.CallbackQuery, cafes_config, state: FSMContext):
    """Шаг 1: Выбор кафе"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=cafe["name"], callback_data=f"add_to_{cafe_key}")]
        for cafe_key, cafe in cafes_config.items()
    ] + [[types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]
    )
    
    await call.message.edit_text(
        "🏪 *Выберите кафе для добавления товара:*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def admin_add_item_step2(call: types.CallbackQuery, state: FSMContext):
    """Шаг 2: Ввод названия товара"""
    cafe_key = call.data.replace("add_to_", "")
    await state.update_data(cafe_key=cafe_key)
    await state.set_state(AdminStates.waiting_for_item_name)
    
    await call.message.edit_text(
        "📝 *Введите название товара:*\n\nПример: `Пицца Пепперони`",
        parse_mode="Markdown"
    )

async def admin_add_item_step3(message: types.Message, state: FSMContext):
    """Шаг 3: Ввод цены"""
    item_name = message.text.strip()
    if not item_name:
        await message.answer("❌ Название не может быть пустым!")
        return
    
    await state.update_data(item_name=item_name)
    await state.set_state(AdminStates.waiting_for_item_price)
    
    await message.answer(
        "💰 *Введите цену товара:*\n\nПример: `550`",
        parse_mode="Markdown"
    )

async def admin_add_item_step4(message: types.Message, state: FSMContext, cafes_config):
    """Шаг 4: Выбор категории и сохранение"""
    try:
        price = int(message.text.strip())
        if price <= 0:
            await message.answer("❌ Цена должна быть больше 0!")
            return
    except:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    cafe_key = data.get("cafe_key")
    item_name = data.get("item_name")
    
    # Загружаем текущее меню
    menus = load_menus()
    if cafe_key not in menus:
        menus[cafe_key] = {"CATEGORIES": {}, "MENU_TEXT": ""}
    
    categories = menus[cafe_key]["CATEGORIES"]
    
    if not categories:
        # Если нет категорий, создаем общую
        categories["🍽️ Основное"] = {}
        await message.answer("ℹ️ Создана общая категория '🍽️ Основное'")
    
    # Показываем категории для выбора
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=cat_name, callback_data=f"cat_{cat_name}")]
        for cat_name in categories.keys()
    ] + [[types.InlineKeyboardButton(text="➕ Новая категория", callback_data="new_category")]]
    )
    
    await state.update_data(price=price)
    await state.set_state(AdminStates.waiting_for_category)
    
    await message.answer(
        f"📁 *Выберите категорию для товара:*\n\n"
        f"Товар: {item_name}\n"
        f"Цена: {price}₽",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def admin_add_item_final(call: types.CallbackQuery, state: FSMContext):
    """Финальный шаг: сохранение товара"""
    data = await state.get_data()
    cafe_key = data.get("cafe_key")
    item_name = data.get("item_name")
    price = data.get("price")
    category = call.data.replace("cat_", "")
    
    # Загружаем и обновляем меню
    menus = load_menus()
    
    if category not in menus[cafe_key]["CATEGORIES"]:
        menus[cafe_key]["CATEGORIES"][category] = {}
    
    menus[cafe_key]["CATEGORIES"][category][item_name] = price
    save_menus(menus)
    
    await state.clear()
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ Добавить еще", callback_data="admin_add_item")],
        [types.InlineKeyboardButton(text="🔙 В админку", callback_data="admin_back")]
    ])
    
    await call.message.edit_text(
        f"✅ *Товар добавлен!*\n\n"
        f"🏪 Кафе: {cafe_key}\n"
        f"📁 Категория: {category}\n"
        f"📝 Товар: {item_name}\n"
        f"💰 Цена: {price}₽",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def admin_create_new_category(message: types.Message, state: FSMContext):
    """Создание новой категории"""
    category_name = message.text.strip()
    if not category_name:
        await message.answer("❌ Название категории не может быть пустым!")
        return
    
    data = await state.get_data()
    cafe_key = data.get("cafe_key")
    item_name = data.get("item_name")
    price = data.get("price")
    
    # Загружаем и обновляем меню
    menus = load_menus()
    
    menus[cafe_key]["CATEGORIES"][category_name] = {item_name: price}
    save_menus(menus)
    
    await state.clear()
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ Добавить еще", callback_data="admin_add_item")],
        [types.InlineKeyboardButton(text="🔙 В админку", callback_data="admin_back")]
    ])
    
    await message.answer(
        f"✅ *Товар добавлен в новую категорию!*\n\n"
        f"📁 Новая категория: {category_name}\n"
        f"📝 Товар: {item_name}\n"
        f"💰 Цена: {price}₽",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ============ ИЗМЕНЕНИЕ ЦЕНЫ ============

async def admin_edit_price_step1(call: types.CallbackQuery, cafes_config):
    """Шаг 1: Выбор товара для изменения цены"""
    menus = load_menus()
    
    keyboard_buttons = []
    for cafe_key, cafe_data in menus.items():
        cafe_name = cafes_config.get(cafe_key, {}).get("name", cafe_key)
        categories = cafe_data.get("CATEGORIES", {})
        
        for cat_name, items in categories.items():
            for item_name in items.keys():
                callback_data = f"edit_price_{cafe_key}_{cat_name}_{item_name}"
                keyboard_buttons.append([
                    types.InlineKeyboardButton(
                        text=f"{cafe_name}: {item_name}",
                        callback_data=callback_data
                    )
                ])
    
    if not keyboard_buttons:
        await call.message.edit_text("📭 Нет товаров для редактирования!")
        return
    
    keyboard_buttons.append([types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    
    await call.message.edit_text(
        "✏️ *Выберите товар для изменения цены:*",
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    )

async def admin_edit_price_step2(call: types.CallbackQuery, state: FSMContext):
    """Шаг 2: Ввод новой цены"""
    parts = call.data.split("_")[2:]  # edit_price_{cafe}_{cat}_{item}
    cafe_key = parts[0]
    category = parts[1]
    item_name = "_".join(parts[2:])
    
    await state.update_data(
        cafe_key=cafe_key,
        category=category,
        item_name=item_name
    )
    await state.set_state(AdminStates.waiting_for_new_price)
    
    menus = load_menus()
    old_price = menus[cafe_key]["CATEGORIES"][category][item_name]
    
    await call.message.edit_text(
        f"💰 *Изменение цены*\n\n"
        f"Товар: {item_name}\n"
        f"Категория: {category}\n"
        f"Текущая цена: {old_price}₽\n\n"
        f"*Введите новую цену:*",
        parse_mode="Markdown"
    )

async def admin_edit_price_final(message: types.Message, state: FSMContext):
    """Финальный шаг: сохранение новой цены"""
    try:
        new_price = int(message.text.strip())
        if new_price <= 0:
            await message.answer("❌ Цена должна быть больше 0!")
            return
    except:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    cafe_key = data.get("cafe_key")
    category = data.get("category")
    item_name = data.get("item_name")
    
    menus = load_menus()
    old_price = menus[cafe_key]["CATEGORIES"][category][item_name]
    menus[cafe_key]["CATEGORIES"][category][item_name] = new_price
    save_menus(menus)
    
    await state.clear()
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✏️ Изменить еще", callback_data="admin_edit_price")],
        [types.InlineKeyboardButton(text="🔙 В админку", callback_data="admin_back")]
    ])
    
    await message.answer(
        f"✅ *Цена изменена!*\n\n"
        f"📝 Товар: {item_name}\n"
        f"💰 Было: {old_price}₽ → Стало: {new_price}₽",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ============ УДАЛЕНИЕ ТОВАРА ============

async def admin_delete_item_step1(call: types.CallbackQuery, cafes_config):
    """Шаг 1: Выбор товара для удаления"""
    menus = load_menus()
    
    keyboard_buttons = []
    for cafe_key, cafe_data in menus.items():
        cafe_name = cafes_config.get(cafe_key, {}).get("name", cafe_key)
        categories = cafe_data.get("CATEGORIES", {})
        
        for cat_name, items in categories.items():
            for item_name in items.keys():
                callback_data = f"delete_{cafe_key}_{cat_name}_{item_name}"
                keyboard_buttons.append([
                    types.InlineKeyboardButton(
                        text=f"{cafe_name}: {item_name}",
                        callback_data=callback_data
                    )
                ])
    
    if not keyboard_buttons:
        await call.message.edit_text("📭 Нет товаров для удаления!")
        return
    
    keyboard_buttons.append([types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    
    await call.message.edit_text(
        "🗑️ *Выберите товар для удаления:*",
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    )

async def admin_delete_item_step2(call: types.CallbackQuery):
    """Шаг 2: Подтверждение удаления"""
    parts = call.data.split("_")[1:]  # delete_{cafe}_{cat}_{item}
    cafe_key = parts[0]
    category = parts[1]
    item_name = "_".join(parts[2:])
    
    menus = load_menus()
    price = menus[cafe_key]["CATEGORIES"][category][item_name]
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_delete_{cafe_key}_{category}_{item_name}"),
            types.InlineKeyboardButton(text="❌ Нет", callback_data="admin_delete_item")
        ]
    ])
    
    await call.message.edit_text(
        f"⚠️ *Подтвердите удаление*\n\n"
        f"Вы точно хотите удалить товар?\n\n"
        f"📝 Товар: {item_name}\n"
        f"📁 Категория: {category}\n"
        f"💰 Цена: {price}₽\n\n"
        f"*Это действие нельзя отменить!*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def admin_delete_item_final(call: types.CallbackQuery):
    """Финальный шаг: удаление товара"""
    parts = call.data.split("_")[2:]  # confirm_delete_{cafe}_{cat}_{item}
    cafe_key = parts[0]
    category = parts[1]
    item_name = "_".join(parts[2:])
    
    menus = load_menus()
    
    # Удаляем товар
    del menus[cafe_key]["CATEGORIES"][category][item_name]
    
    # Если категория пустая, удаляем её
    if not menus[cafe_key]["CATEGORIES"][category]:
        del menus[cafe_key]["CATEGORIES"][category]
    
    save_menus(menus)
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🗑️ Удалить еще", callback_data="admin_delete_item")],
        [types.InlineKeyboardButton(text="🔙 В админку", callback_data="admin_back")]
    ])
    
    await call.message.edit_text(
        f"✅ *Товар удален!*\n\n"
        f"🗑️ Удален: {item_name}",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ============ ДОБАВЛЕНИЕ КАТЕГОРИИ ============

async def admin_add_category(message: types.Message, cafes_config):
    """Добавление новой категории"""
    # Простое добавление категории в первое кафе
    menus = load_menus()
    
    if not menus:
        await message.answer("❌ Сначала добавьте товар в кафе!")
        return
    
    # Берем первое кафе
    cafe_key = list(menus.keys())[0]
    
    # Создаем новую категорию
    new_category = "📁 Новая категория"
    if new_category not in menus[cafe_key]["CATEGORIES"]:
        menus[cafe_key]["CATEGORIES"][new_category] = {}
        save_menus(menus)
        
        await message.answer(
            f"✅ *Категория добавлена!*\n\n"
            f"🏪 Кафе: {cafe_key}\n"
            f"📁 Категория: {new_category}\n\n"
            f"Теперь добавьте товары в эту категорию.",
            parse_mode="Markdown"
        )
    else:
        await message.answer("ℹ️ Категория уже существует")

# ============ ОБРАБОТЧИК НАЗАД ============

async def admin_back(call: types.CallbackQuery, cafes_config):
    """Вернуться в админ-панель"""
    await show_admin_panel(call.message, cafes_config)