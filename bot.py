import os
import importlib
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, CAFES, DEFAULT_CAFE
from ai_brain import ask_grok

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_cart = defaultdict(list)
ai_mode = defaultdict(bool)
user_cafe = defaultdict(lambda: DEFAULT_CAFE)

def load_menu(cafe_key):
    """Загружает меню для конкретного кафе"""
    try:
        if cafe_key not in CAFES:
            cafe_key = DEFAULT_CAFE
            
        cafe_config = CAFES[cafe_key]
        module_path = cafe_config["menu_file"]
        
        menu_module = importlib.import_module(module_path)
        return menu_module.CATEGORIES, menu_module.ALL_ITEMS, menu_module.MENU_TEXT
    except Exception as e:
        print(f"Ошибка загрузки меню для {cafe_key}: {e}")
        default_module = importlib.import_module(CAFES[DEFAULT_CAFE]["menu_file"])
        return default_module.CATEGORIES, default_module.ALL_ITEMS, default_module.MENU_TEXT

@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    ai_mode[user_id] = False
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍝 Итальянское кафе", callback_data="cafe_italy")],
        [InlineKeyboardButton(text="🍣 Суши-бар", callback_data="cafe_sushi")],
        [InlineKeyboardButton(text="🍔 Бургер-хаус", callback_data="cafe_burger")],
    ])
    
    await message.answer(
        "🏪 *ДОБРО ПОЖАЛОВАТЬ!*\n\n"
        "Выбери кафе, из которого хочешь заказать:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data.startswith("cafe_"))
async def select_cafe(call: types.CallbackQuery):
    user_id = call.from_user.id
    cafe_key = call.data[5:]
    
    if cafe_key in CAFES:
        user_cafe[user_id] = cafe_key
        cafe_name = CAFES[cafe_key]["name"]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Меню", callback_data="menu")],
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
            [InlineKeyboardButton(text="🤖 AI-Помощник", callback_data="chat_mode")],
            [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
        ])
        
        await call.message.edit_text(
            f"🏪 {cafe_name}\n\n"
            "Готов принимать ваш заказ! Что желаете?",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    await call.answer()

@dp.callback_query(lambda c: c.data == "change_cafe")
async def change_cafe(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_cart[user_id] = []
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍝 Итальянское кафе", callback_data="cafe_italy")],
        [InlineKeyboardButton(text="🍣 Суши-бар", callback_data="cafe_sushi")],
        [InlineKeyboardButton(text="🍔 Бургер-хаус", callback_data="cafe_burger")],
    ])
    
    await call.message.edit_text(
        "🏪 *СМЕНА КАФЕ*\n\n"
        "Корзина очищена! Выбери новое кафе:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "menu")
async def show_categories(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = False
    
    cafe_key = user_cafe[user_id]
    CATEGORIES, ALL_ITEMS, MENU_TEXT = load_menu(cafe_key)
    
    keyboard = []
    for category_name in CATEGORIES.keys():
        keyboard.append([InlineKeyboardButton(text=category_name, callback_data=f"category_{category_name.replace(' ', '_')}")])
    
    keyboard += [
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
        [InlineKeyboardButton(text="🤖 AI-Помощник", callback_data="chat_mode")],
        [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
    ]
    
    await call.message.edit_text(
        text=MENU_TEXT,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("category_"))
async def show_category_items(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = False
    
    cafe_key = user_cafe[user_id]
    CATEGORIES, ALL_ITEMS, _ = load_menu(cafe_key)
    
    category_key = call.data[9:].replace('_', ' ')
    full_category_name = None
    
    for cat_name in CATEGORIES.keys():
        if cat_name.replace(' ', '_') == category_key.replace(' ', '_'):
            full_category_name = cat_name
            break
    
    if not full_category_name:
        await call.answer("Категория не найдена")
        return
    
    items = CATEGORIES[full_category_name]
    keyboard = []
    items_list = list(items.items())
    
    for i in range(0, len(items_list), 2):
        row = []
        for j in range(2):
            if i + j < len(items_list):
                item_name, price = items_list[i + j]
                row.append(InlineKeyboardButton(
                    text=f"{item_name} — {price}₽",
                    callback_data=f"add_{item_name}"
                ))
        keyboard.append(row)
    
    keyboard += [
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
    ]
    
    await call.message.edit_text(
        text=f"*{full_category_name}*\n\nВыбирай вкусняшку:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    cafe_key = user_cafe[user_id]
    _, ALL_ITEMS, _ = load_menu(cafe_key)
    
    item_name = call.data[4:]
    if item_name in ALL_ITEMS:
        user_cart[user_id].append({
            "name": item_name, 
            "price": ALL_ITEMS[item_name],
            "cafe": cafe_key
        })
        await call.answer(f"{item_name} — в корзине!", show_alert=True)
    else:
        await call.answer("Такого нет в меню")

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = False
    
    cart_items = user_cart[user_id]
    cafe_key = user_cafe[user_id]
    cafe_name = CAFES[cafe_key]["name"]
    
    if not cart_items:
        text = f"*{cafe_name}*\n\n🛒 *Корзина пустая!*\n\n"
        keyboard = [
            [InlineKeyboardButton(text="📖 Перейти в меню", callback_data="menu")],
            [InlineKeyboardButton(text="🤖 AI-Помощник", callback_data="chat_mode")],
            [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
        ]
    else:
        total = sum(item["price"] for item in cart_items)
        text = f"*{cafe_name}*\n\n🛒 *Твоя корзина:*\n\n"
        counts = {}
        for item in cart_items:
            name = item["name"]
            counts[name] = counts.get(name, 0) + 1
        
        for name, cnt in counts.items():
            price = counts[name] * next(item["price"] for item in cart_items if item["name"] == name)
            text += f"× {name} × {cnt} = {price}₽\n"
        
        text += f"\n*Итого: {total}₽*"
        keyboard = [
            [InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="📖 В меню", callback_data="menu")],
            [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
        ]
    
    await call.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_cart[user_id].clear()
    await call.answer("Корзина очищена!")
    await show_cart(call)

@dp.callback_query(lambda c: c.data == "checkout")
async def checkout(call: types.CallbackQuery):
    user_id = call.from_user.id
    cart_items = user_cart[user_id].copy()
    user_cart[user_id].clear()
    
    if not cart_items:
        await call.answer("Корзина пустая!")
        return
    
    cafe_key = user_cafe[user_id]
    cafe_name = CAFES[cafe_key]["name"]
    total = sum(item["price"] for item in cart_items)
    
    order_text = f"🏪 *ЗАКАЗ ИЗ {cafe_name.upper()}*\n\n"
    counts = {}
    for item in cart_items:
        name = item["name"]
        counts[name] = counts.get(name, 0) + 1
    
    for name, cnt in counts.items():
        price = counts[name] * next(item["price"] for item in cart_items if item["name"] == name)
        order_text += f"• {name} × {cnt} = {price}₽\n"
    
    order_text += f"\n*Сумма: {total}₽*\n"
    order_text += "Менеджер свяжется с вами в ближайшее время!"
    
    await call.message.edit_text(
        text=order_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Сделать новый заказ", callback_data="menu")]
        ]),
        parse_mode="Markdown"
    )
    await call.answer("Заказ отправлен!")

# Остальные функции AI остаются как были
@dp.callback_query(lambda c: c.data == "chat_mode")
async def enable_chat_mode(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = True
    cafe_key = user_cafe[user_id]
    cafe_name = CAFES[cafe_key]["name"]
    
    await call.message.edit_text(
        f"🏪 {cafe_name}\n\n"
        "*AI-ПОМОЩНИК ВКЛЮЧЁН!*\n\n"
        "Теперь просто пиши, что хочешь:\n\n"
        "• Две пепперони и колу\n"
        "• Покажи корзину\n" 
        "• Очисти всё\n"
        "• Что посоветуешь?\n\n"
        "Я всё пойму!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Вернуться в меню", callback_data="menu")],
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
            [InlineKeyboardButton(text="❌ Выключить AI", callback_data="disable_ai")]
        ]),
        parse_mode="Markdown"
    )
    await call.answer("AI включён!")

@dp.callback_query(lambda c: c.data == "disable_ai")
async def disable_ai_mode(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = False
    cafe_key = user_cafe[user_id]
    cafe_name = CAFES[cafe_key]["name"]
    
    await call.message.edit_text(
        f"🏪 {cafe_name}\n\n"
        "*AI-ПОМОЩНИК ВЫКЛЮЧЕН*\n\n"
        "Используй кнопки ниже",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Меню", callback_data="menu")],
            [InlineKeyboardButton(text="🤖 AI-Помощник", callback_data="chat_mode")],
            [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
        ]),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    cafe_key = user_cafe[user_id]
    _, ALL_ITEMS, _ = load_menu(cafe_key)
    
    if text in ALL_ITEMS:
        user_cart[user_id].append({
            "name": text, 
            "price": ALL_ITEMS[text],
            "cafe": cafe_key
        })
        await message.answer(f"{text} — добавлено в корзину!")
        return
    
    if ai_mode.get(user_id, False):
        cart_items = user_cart[user_id]
        cart_info = "пустая"
        if cart_items:
            total = sum(i["price"] for i in cart_items)
            counts = defaultdict(int)
            for i in cart_items:
                counts[i["name"]] += 1
            cart_info = ", ".join(f"{n}×{c}" for n, c in counts.items()) + f" → {total}₽"
        
        response = await ask_grok(text, cart_info)
        await message.answer(
            f"*AI:* {response}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📖 Меню", callback_data="menu")],
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
                [InlineKeyboardButton(text="🤖 Чат с AI", callback_data="chat_mode")]
            ])
        )
    else:
        await message.answer(
            "Не понял команду\n"
            "Нажми на кнопки или включи AI",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📖 Меню", callback_data="menu")],
                [InlineKeyboardButton(text="🤖 AI-Помощник", callback_data="chat_mode")]
            ])
        )

async def main():
    print("🏪 Универсальный бот для всех кафе запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
