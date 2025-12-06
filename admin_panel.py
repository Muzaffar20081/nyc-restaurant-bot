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
    waiting_for_new_category = State()

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

# ============ АДМИН КОМАНДЫ ============

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
    """Шаг 2: Выбор кафе завершен, запрос названия товара"""
    cafe_key = call.data.replace("add_to_", "")
    await state.update_data(cafe_key=cafe_key)
    await state.set_state(AdminStates.waiting_for_item_name)
    
    await call.message.edit_text(
        "📝 *Введите название товара:*\n\nПример: `Пицца Пепперони`",
        parse_mode="Markdown"
    )

async def admin_add_item_step3(message: types.Message, state: FSMContext):
    """Шаг 3: Ввод названия товара"""
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

async def admin_add_item_step4(message: types.Message, state: FSMContext, cafes_config):
    """Шаг 4: Ввод цены и выбор категории"""
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
    keyboard_buttons = []
    for cat_name in categories.keys():
        callback_data = f"cat_select_{cafe_key}_{cat_name}"
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
    
    await state.update_data(price=price, item_name=item_name, cafe_key=cafe_key)
    await state.set_state(AdminStates.waiting_for_category)
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(
        f"📁 *Выберите категорию для товара:*\n\n"
        f"🏪 Кафе: {cafes_config.get(cafe_key, {}).get('name', cafe_key)}\n"
        f"📝 Товар: {item_name}\n"
        f"💰 Цена: {price}₽",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def admin_add_item_final(call: types.CallbackQuery, state: FSMContext):
    """Финальный шаг: сохранение товара в выбранную категорию"""
    # Формат: cat_select_{cafe_key}_{category_name}
    parts = call.data.split('_')
    if len(parts) >= 4:
        cafe_key = parts[2]
        category_name = '_'.join(parts[3:])
    else:
        await call.answer("❌ Ошибка данных", show_alert=True)
        return
    
    data = await state.get_data()
    item_name = data.get("item_name")
    price = data.get("price")
    
    # Загружаем и обновляем меню
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
        f"🏪 Кафе: {cafe_key}\n"
        f"📁 Категория: {category_name}\n"
        f"📝 Товар: {item_name}\n"
        f"💰 Цена: {price}₽",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def admin_create_new_category_for_item(call: types.CallbackQuery, state: FSMContext):
    """Создание новой категории для товара"""
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

async def admin_save_new_category_with_item(message: types.Message, state: FSMContext):
    """Сохранение товара в новую категорию"""
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
        f"🏪 Кафе: {cafe_key}\n"
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
    
    if not menus:
        await call.message.edit_text("📭 Нет товаров для редактирования!")
        return
    
    keyboard_buttons = []
    for cafe_key, cafe_data in menus.items():
        cafe_name = cafes_config.get(cafe_key, {}).get("name", cafe_key)
        categories = cafe_data.get("CATEGORIES", {})
        
        for cat_name, items in categories.items():
            for item_name in items.keys():
                # Безопасное кодирование
                safe_data = f"edit_price:{cafe_key}:{cat_name}:{item_name}"
                keyboard_buttons.append([
                    types.InlineKeyboardButton(
                        text=f"{cafe_name}: {item_name}",
                        callback_data=safe_data
                    )
                ])
    
    if not keyboard_buttons:
        await call.message.edit_text("📭 Нет товаров для редактирования!")
        return
    
    # Добавляем кнопки пагинации (если много товаров)
    keyboard_buttons.append([types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    
    await call.message.edit_text(
        "✏️ *Выберите товар для изменения цены:*",
        parse_mode="Markdown",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    )

async def admin_edit_price_step2(call: types.CallbackQuery, state: FSMContext):
    """Шаг 2: Ввод новой цены"""
    # Формат: edit_price:{cafe_key}:{category}:{item_name}
    parts = call.data.split(':')
    if len(parts) < 4:
        await call.answer("❌ Ошибка данных", show_alert=True)
        return
    
    cafe_key = parts[1]
    category = parts[2]
    item_name = ':'.join(parts[3:])  # На случай, если в названии есть :
    
    await state.update_data(
        cafe_key=cafe_key,
        category=category,
        item_name=item_name
    )
    await state.set_state(AdminStates.waiting_for_new_price)
    
    menus = load_menus()
    old_price = menus.get(cafe_key, {}).get("CATEGORIES", {}).get(category, {}).get(item_name, "?")
    
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
        if new_price > 100000:
            await message.answer("❌ Цена слишком большая!")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    cafe_key = data.get("cafe_key")
    category = data.get("category")
    item_name = data.get("item_name")
    
    menus = load_menus()
    
    if (cafe_key in menus and 
        category in menus[cafe_key]["CATEGORIES"] and 
        item_name in menus[cafe_key]["CATEGORIES"][category]):
        
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
    else:
        await message.answer("❌ Товар не найден!")

# ============ УДАЛЕНИЕ ТОВАРА ============

async def admin_delete_item_step1(call: types.CallbackQuery, cafes_config):
    """Шаг 1: Выбор товара для удаления"""
    menus = load_menus()
    
    if not menus:
        await call.message.edit_text("📭 Нет товаров для удаления!")
        return
    
    keyboard_buttons = []
    for cafe_key, cafe_data in menus.items():
        cafe_name = cafes_config.get(cafe_key, {}).get("name", cafe_key)
        categories = cafe_data.get("CATEGORIES", {})
        
        for cat_name, items in categories.items():
            for item_name in items.keys():
                # Безопасное кодирование
                safe_data = f"delete_item:{cafe_key}:{cat_name}:{item_name}"
                keyboard_buttons.append([
                    types.InlineKeyboardButton(
                        text=f"{cafe_name}: {item_name}",
                        callback_data=safe_data
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
    # Формат: delete_item:{cafe_key}:{category}:{item_name}
    parts = call.data.split(':')
    if len(parts) < 4:
        await call.answer("❌ Ошибка данных", show_alert=True)
        return
    
    cafe_key = parts[1]
    category = parts[2]
    item_name = ':'.join(parts[3:])
    
    menus = load_menus()
    price = menus.get(cafe_key, {}).get("CATEGORIES", {}).get(category, {}).get(item_name, "?")
    
    # Кодируем данные для подтверждения
    confirm_data = f"confirm_delete:{cafe_key}:{category}:{item_name}"
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ Да, удалить", callback_data=confirm_data),
            types.InlineKeyboardButton(text="❌ Нет, отмена", callback_data="admin_delete_item")
        ]
    ])
    
    await call.message.edit_text(
        f"⚠️ *Подтвердите удаление*\n\n"
        f"Вы точно хотите удалить товар?\n\n"
        f"🏪 Кафе: {cafe_key}\n"
        f"📁 Категория: {category}\n"
        f"📝 Товар: {item_name}\n"
        f"💰 Цена: {price}₽\n\n"
        f"*Это действие нельзя отменить!*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def admin_delete_item_final(call: types.CallbackQuery):
    """Финальный шаг: удаление товара"""
    # Формат: confirm_delete:{cafe_key}:{category}:{item_name}
    parts = call.data.split(':')
    if len(parts) < 4:
        await call.answer("❌ Ошибка данных", show_alert=True)
        return
    
    cafe_key = parts[1]
    category = parts[2]
    item_name = ':'.join(parts[3:])
    
    menus = load_menus()
    
    # Проверяем существование
    if (cafe_key in menus and 
        category in menus[cafe_key]["CATEGORIES"] and 
        item_name in menus[cafe_key]["CATEGORIES"][category]):
        
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
            f"🗑️ Удален: {item_name}\n"
            f"📁 Категория: {category}",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    else:
        await call.answer("❌ Товар не найден", show_alert=True)

# ============ ДОБАВЛЕНИЕ КАТЕГОРИИ ============

async def admin_add_category(call: types.CallbackQuery, cafes_config, state: FSMContext):
    """Добавление новой категории"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=cafe["name"], callback_data=f"add_cat_to_{cafe_key}")]
        for cafe_key, cafe in cafes_config.items()
    ] + [[types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]]
    )
    
    await call.message.edit_text(
        "🏪 *Выберите кафе для добавления категории:*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def admin_add_category_step2(call: types.CallbackQuery, state: FSMContext):
    """Шаг 2: Ввод названия категории"""
    cafe_key = call.data.replace("add_cat_to_", "")
    await state.update_data(cafe_key=cafe_key)
    await state.set_state(AdminStates.waiting_for_new_category)
    
    await call.message.edit_text(
        "📝 *Введите название новой категории:*\n\n"
        "Пример: `🍕 Пицца`, `🥤 Напитки`, `🍰 Десерты`",
        parse_mode="Markdown"
    )

async def admin_save_new_category(message: types.Message, state: FSMContext, cafes_config):
    """Сохранение новой категории"""
    category_name = message.text.strip()
    if not category_name:
        await message.answer("❌ Название категории не может быть пустым!")
        return
    
    data = await state.get_data()
    cafe_key = data.get("cafe_key")
    
    menus = load_menus()
    
    if cafe_key not in menus:
        menus[cafe_key] = {"CATEGORIES": {}, "MENU_TEXT": ""}
    
    if category_name in menus[cafe_key]["CATEGORIES"]:
        await message.answer(f"❌ Категория '{category_name}' уже существует!")
        return
    
    menus[cafe_key]["CATEGORIES"][category_name] = {}
    save_menus(menus)
    
    cafe_name = cafes_config.get(cafe_key, {}).get("name", cafe_key)
    
    await state.clear()
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📁 Добавить еще", callback_data="admin_add_category")],
        [types.InlineKeyboardButton(text="🔙 В админку", callback_data="admin_back")]
    ])
    
    await message.answer(
        f"✅ *Категория добавлена!*\n\n"
        f"🏪 Кафе: {cafe_name}\n"
        f"📁 Категория: {category_name}\n\n"
        f"Теперь добавьте товары в эту категорию.",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ============ ОБРАБОТЧИК НАЗАД ============

async def admin_back(call: types.CallbackQuery, cafes_config):
    """Вернуться в админ-панель"""
    await show_admin_panel(call.message, cafes_config)
