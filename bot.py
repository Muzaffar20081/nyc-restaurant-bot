# bot.py — МУЛЬТИ-КАФЕ БОТ 2025 (полностью готов к запуску)

import importlib
from collections import defaultdict
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN
from ai_brain import ask_grok

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилища
user_cart = defaultdict(list)
ai_mode = defaultdict(bool)
user_cafe = {}  # user_id → модуль кафе

# Автообнаружение всех кафе в папке cafes/
import os
import glob
CAFE_MODULES = {}
for file in glob.glob("cafes/*.py"):
    if file.endswith("__init__.py"):
        continue
    module_name = os.path.basename(file)[:-3]  # без .py
    CAFE_MODULES[module_name] = f"cafes.{module_name}"

def load_cafe(key: str):
    key = key.lower()
    if key not in CAFE_MODULES:
        key = "mycafe"  # дефолтное кафе
    return importlib.import_module(CAFE_MODULES[key])

def get_cafe(user_id):
    if user_id not in user_cafe or user_cafe[user_id] is None:
        user_cafe[user_id] = load_cafe("mycafe")
    return user_cafe[user_id]

# ====================== СТАРТ ======================
@dp.message(CommandStart())
async def start_default(message: types.Message):
    kb = []
    for key, path in CAFE_MODULES.items():
        module = importlib.import_module(path)
        name = getattr(module, "NAME", key.title())
        kb.append([InlineKeyboardButton(text=f"{name}", callback_data=f"select_{key}")])
    
    await message.answer(
        "*Выбери своё кафе*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

@dp.message(CommandStart(deep_link=True))
async def start_with_cafe(message: types.Message, command_args: str):
    cafe_key = command_args.lower() if command_args else "mycafe"
    user_cafe[message.from_user.id] = load_cafe(cafe_key)
    await show_welcome(message)

@dp.callback_query(F.data.startswith("select_"))
async def select_cafe(call: types.CallbackQuery):
    cafe_key = call.data.split("_", 1)[1]
    user_cafe[call.from_user.id] = load_cafe(cafe_key)
    await show_welcome(call.message, edit=True)
    await call.answer()

async def show_welcome(message_or_call, edit=False):
    user_id = message_or_call.from_user.id
    cafe = get_cafe(user_id)
    text = f"*{cafe.WELCOME_TEXT}*\n\nПривет, {message_or_call.from_user.first_name}!\nГотов заказать вкусняшку?"

    kb = [
        [InlineKeyboardButton(text="Меню", callback_data="menu")],
        [InlineKeyboardButton(text="Корзина", callback_data="cart")],
        [InlineKeyboardButton(text="AI-Помощник", callback_data="chat_mode")]
    ]

    if edit:
        await message_or_call.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    else:
        await message_or_call.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ====================== МЕНЮ ======================
@dp.callback_query(F.data == "menu")
async def show_categories(call: types.CallbackQuery):
    cafe = get_cafe(call.from_user.id)
    ai_mode[call.from_user.id] = False

    kb = []
    for cat in cafe.CATEGORIES.keys():
        kb.append([InlineKeyboardButton(text=cat, callback_data=f"cat_{cat[2:] if cat.startswith('') else cat}")])

    kb += [
        [InlineKeyboardButton(text="Корзина", callback_data="cart")],
        [InlineKeyboardButton(text="AI-Помощник", callback_data="chat_mode")]
    ]

    await call.message.edit_text(
        "*МЕНЮ*\nВыбери категорию:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await call.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def show_category_items(call: types.CallbackQuery):
    cafe = get_cafe(call.from_user.id)
    key = call.data[4:]
    full_name = next((name for name in cafe.CATEGORIES if name[2:].strip() == key), None)
    if not full_name:
        await call.answer("Категория не найдена")
        return

    items = cafe.CATEGORIES[full_name]
    kb = []
    for i, (name, price) in enumerate(items.items()):
        if i % 2 == 0:
            kb.append([])
        kb[-1].append(InlineKeyboardButton(text=f"{name} — {price}₽", callback_data=f"add_{name}"))

    kb += [
        [InlineKeyboardButton(text="Назад", callback_data="menu")],
        [InlineKeyboardButton(text="Корзина", callback_data="cart")]
    ]

    await call.message.edit_text(
        f"*{full_name}*\n\nВыбери блюдо:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await call.answer()

# ====================== КОРЗИНА И ЗАКАЗ ======================
@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(call: types.CallbackQuery):
    cafe = get_cafe(call.from_user.id)
    item = call.data[4:]
    if item in cafe.ALL_ITEMS:
        user_cart[call.from_user.id].append({"name": item, "price": cafe.ALL_ITEMS[item]})
        await call.answer(f"{item} добавлено!")
    else:
        await call.answer("Товара нет")

@dp.callback_query(F.data == "cart")
async def show_cart(call: types.CallbackQuery):
    cafe = get_cafe(call.from_user.id)
    ai_mode[call.from_user.id] = False
    items = user_cart[call.from_user.id]

    if not items:
        kb = [[InlineKeyboardButton(text="Меню", callback_data="menu")]]
        await call.message.edit_text("*Корзина пустая!*\nДобавь что-нибудь", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
        await call.answer()
        return

    total = sum(x["price"] for x in items)
    counts = defaultdict(int)
    for x in items:
        counts[x["name"]] += 1

    text = "*Твоя корзина:*\n\n"
    for name, cnt in counts.items():
        text += f"• {name} × {cnt} = {cafe.ALL_ITEMS[name] * cnt}₽\n"
    text += f"\n*Итого: {total}₽*"

    kb = [
        [InlineKeyboardButton(text="Очистить", callback_data="clear")],
        [InlineKeyboardButton(text="Заказать", callback_data="checkout")],
        [InlineKeyboardButton(text="Назад", callback_data="menu")]
    ]

    await call.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await call.answer()

@dp.callback_query(F.data == "clear")
async def clear_cart(call: types.CallbackQuery):
    user_cart[call.from_user.id].clear()
    await call.answer("Корзина очищена!")
    await show_cart(call)

@dp.callback_query(F.data == "checkout")
async def checkout(call: types.CallbackQuery):
    items = user_cart[call.from_user.id].copy()
    user_cart[call.from_user.id].clear()
    total = sum(x["price"] for x in items)

    text = "*Заказ принят!*\n\n"
    for x in items:
        text += f"• {x['name']} — {x['price']}₽\n"
    text += f"\n*Сумма: {total}₽*\nСкоро с вами свяжемся!"

    await call.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Новый заказ", callback_data="menu")]])
    )
    await call.answer("Заказ отправлен!")

# ====================== AI РЕЖИМ ======================
@dp.callback_query(F.data == "chat_mode")
async def enable_ai(call: types.CallbackQuery):
    ai_mode[call.from_user.id] = True
    await call.message.edit_text(
        "*AI-ПОМОЩНИК ВКЛЮЧЁН!*\n\nПиши что угодно — я пойму:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")],
            [InlineKeyboardButton(text="Выключить AI", callback_data="disable_ai")]
        ])
    )
    await call.answer("AI включён!")

@dp.callback_query(F.data == "disable_ai")
async def disable_ai(call: types.CallbackQuery):
    ai_mode[call.from_user.id] = False
    await call.message.edit_text("*AI выключен*\nИспользуй кнопки", parse_mode="Markdown")
    await call.answer()

@dp.message()
async def handle_text(message: types.Message):
    cafe = get_cafe(message.from_user.id)
    text = message.text.strip()

    if text in cafe.ALL_ITEMS:
        user_cart[message.from_user.id].append({"name": text, "price": cafe.ALL_ITEMS[text]})
        await message.answer(f"{text} добавлено в корзину!")
        return

    if ai_mode.get(message.from_user.id, False):
        cart_info = "пустая"
        if user_cart[message.from_user.id]:
            counts = defaultdict(int)
            for x in user_cart[message.from_user.id]:
                counts[x["name"]] += 1
            total = sum(x["price"] for x in user_cart[message.from_user.id])
            cart_info = ", ".join(f"{n}×{c}" for n, c in counts.items()) + f" → {total}₽"

        response = await ask_grok(text, cart_info)
        await message.answer(f"*AI:* {response}", parse_mode="Markdown")
    else:
        await message.answer("Не понял! Включи AI или жми кнопки")

# ====================== ЗАПУСК ======================
async def main():
    print("МУЛЬТИ-КАФЕ БОТ ЗАПУЩЕН! ГОТОВ К ЗАКАЗАМ")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
