# bot.py
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F
from config import BOT_TOKEN
from menu import CATEGORIES, ALL_ITEMS, MENU_TEXT
from ai_brain import ask_grok

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_cart = defaultdict(list)
ai_mode = defaultdict(bool)

# Вспомогательная функция: ключ → полное название категории
def get_category_display_name(key: str) -> str:
    for full_name in CATEGORIES.keys():
        if full_name.lower().replace(" ", "_").replace("пицца", "").strip() == key:
            return full_name
    return key.replace("_", " ").title()

@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    ai_mode[user_id] = False

    await message.answer(
        f"Добро пожаловать! \n\n"
        f"Привет, {message.from_user.first_name}!\n"
        f"Заказывай еду прямо тут!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")],
            [InlineKeyboardButton(text="AI Режим", callback_data="chat_mode")]
        ])
    )

@dp.callback_query(F.data == "menu")
async def show_categories(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = False

    keyboard = []
    for category_name in CATEGORIES.keys():
        # Создаём "чистый" ключ без эмодзи и пробелов
        key = category_name.lower()
        key = ''.join(c for c in key if c.isalnum() or c in "_")
        keyboard.append([InlineKeyboardButton(text=category_name, callback_data=f"cat_{key}")])

    keyboard.appendvali([InlineKeyboardButton(text="Корзина", callback_data="cart")])
    keyboard.append([InlineKeyboardButton(text="AI Режим", callback_data="chat_mode")])

    await call.message.edit_text(
        text=MENU_TEXT,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
    await call.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def show_category_items(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = False

    key = call.data[4:]  # после "cat_"
    items = None
    display_name = "Меню"

    for cat_name, cat_items in CATEGORIES.items():
        clean_key = ''.join(c for c in cat_name.lower() if c.isalnum() or c in "_")
        if clean_key == key:
            items = cat_items
            display_name = cat_name
            break

    if not items:
        await call.answer("Категория не найдена", show_alert=True)
        return

    keyboard = []
    item_pairs = list(items.items())
    for i in range(0, len(item_pairs), 2):
        row = []
        for j in range(2):
            if i + j < len(item_pairs):
                name, price = item_pairs[i + j]
                row.append(InlineKeyboardButton(
                    text=f"{name} — {price}₽",
                    callback_data=f"add_{name}"
                ))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="Назад", callback_data="menu")])
    keyboard.append([InlineKeyboardButton(text="Корзина", callback_data="cart")])

    await call.message.edit_text(
        text=f"<b>{display_name}</b>\n\nВыбери блюдо:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
    await call.answer()

@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(call: types.CallbackQuery):
    item_name = call.data[4:]
    user_id = call.from_user.id

    if item_name not in ALL_ITEMS:
        await call.answer("Такого блюда нет!", show_alert=True)
        return

    user_cart[user_id].append({"name": item_name, "price": ALL_ITEMS[item_name]})
    await call.answer(f"{item_name} добавлено в корзину!")

# === Остальные хендлеры (cart, checkout, ai_mode и т.д.) оставляем как у тебя ===
# Они уже отличные, просто меняем parse_mode на HTML и мелкие правки текста

@dp.callback_query(F.data == "cart")
async def show_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = False
    cart_items = user_cart[user_id]

    if not cart_items:
        text = "<b>Корзина пуста!</b>\n\nДобавь что-нибудь вкусное"
        kb = [[InlineKeyboardButton(text="Меню", callback_data="menu")]]
    else:
        total = sum(item["price"] for item in cart_items)
        counts = defaultdict(int)
        for item in cart_items:
            counts[item["name"]] += 1

        text = "<b>Твоя корзина:</b>\n\n"
        for name, cnt in counts.items():
            price = ALL_ITEMS[name] * cnt
            text += f"• {name} × {cnt} = {price}₽\n"
        text += f"\n<b>Итого: {total}₽</b>"

        kb = [
            [InlineKeyboardButton(text="Очистить", callback_data="clear_cart")],
            [InlineKeyboardButton(text="Оформить", callback_data="checkout")],
            [InlineKeyboardButton(text="Назад в меню", callback_data="menu")]
        ]

    await call.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await call.answer()

# (остальные хендлеры: clear_cart, checkout, chat_mode, disable_ai — оставь как у тебя,
# только замени parse_mode="Markdown" → parse_mode="HTML" и экранируй < > где нужно)

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Если просто написал название блюда — добавляем
    if text in ALL_ITEMS:
        user_cart[user_id].append({"name": text, "price": ALL_ITEMS[text]})
        await message.answer(f"{text} добавлено в корзину!")
        return

    if ai_mode.get(user_id, False):
        # Формируем инфу о корзине
        cart_items = user_cart[user_id]
        if cart_items:
            counts = defaultdict(int)
            for it in cart_items:
                counts[it["name"]] += 1
            cart_str = ", ".join(f"{n}×{c}" for n, c in counts.items())
            total = sum(it["price"] for it in cart_items)
            cart_info = f"{cart_str} (итого {total}₽)"
        else:
            cart_info = "пустая"

        response = await ask_grok(text, cart_info)
        await message.answer(
            f"<b>Бот:</b> {response}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Меню", callback_data="menu")],
                [InlineKeyboardButton(text="Корзина", callback_data="cart")],
                [InlineKeyboardButton(text="Продолжить чат", callback_data="chat_mode")]
            ])
        )
    else:
        await message.answer(
            "Не понял команду\n"
            "Нажми на кнопки или включи AI-режим",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Меню", callback_data="menu")],
                [InlineKeyboardButton(text="Включить AI", callback_data="chat_mode")]
            ])
        )

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
