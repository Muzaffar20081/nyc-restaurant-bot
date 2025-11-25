# bot.py — САМЫЙ КРАСИВЫЙ БОТ ДЛЯ КАФЕ

import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN
from menu import CATEGORIES, ALL_ITEMS, MENU_TEXT
from ai_brain import ask_grok

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_cart = defaultdict(list)
ai_mode = defaultdict(bool)


@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    ai_mode[user_id] = False

    await message.answer(
        "ДОБРО ПОЖАЛОВАТЬ В НАШЕ КАФЕ!\n\n"
        f"Привет, {message.from_user.first_name}!\n"
        "Горячая еда, быстрый заказ — всё здесь\n"
        "Выбирай, что хочешь — и погнали!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")],
            [InlineKeyboardButton(text="AI-Помощник", callback_data="chat_mode")]
        ])
    )


@dp.callback_query(lambda c: c.data == "menu")
async def show_categories(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = False

    keyboard = []
    for category_name in CATEGORIES.keys():
        keyboard.append([InlineKeyboardButton(text=category_name, callback_data=f"category_{category_name[2:]}")])

    keyboard += [
        [InlineKeyboardButton(text="Корзина", callback_data="cart")],
        [InlineKeyboardButton(text="AI-Помощник", callback_data="chat_mode")]
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

    category_key = call.data[9:]
    full_category_name = None
    for cat_name in CATEGORIES.keys():
        if cat_name[2:] == category_key:
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
        [InlineKeyboardButton(text="Назад в меню", callback_data="menu")],
        [InlineKeyboardButton(text="Корзина", callback_data="cart")]
    ]

    await call.message.edit_text(
        text=f"*{full_category_name}*\n\n"
             "Выбирай вкусняшку:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(call: types.CallbackQuery):
    item_name = call.data[4:]
    user_id = call.from_user.id

    if item_name in ALL_ITEMS:
        user_cart[user_id].append({"name": item_name, "price": ALL_ITEMS[item_name]})
        await call.answer(f"{item_name} — в корзине!", show_alert=True)
    else:
        await call.answer("Такого нет в меню")


@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = False
    cart_items = user_cart[user_id]

    if not cart_items:
        text = "*Корзина пустая!*\n\n"
        keyboard = [
            [InlineKeyboardButton(text="Перейти в меню", callback_data="menu")],
            [InlineKeyboardButton(text="AI-Помощник", callback_data="chat_mode")]
        ]
    else:
        total = sum(item["price"] for item in cart_items)
        text = "*Твоя корзина:*\n\n"

        counts = {}
        for item in cart_items:
            name = item["name"]
            counts[name] = counts.get(name, 0) + 1

        for name, cnt in counts.items():
            price = ALL_ITEMS[name] * cnt
            text += f"× {name} × {cnt} = {price}₽\n"

        text += f"\n*Итого: {total}₽*"

        keyboard = [
            [InlineKeyboardButton(text="Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="В меню", callback_data="menu")]
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

    total = sum(item["price"] for item in cart_items)

    order_text = "*Заказ принят!*\n\n"
    for item in cart_items:
        order_text += f"• {item['name']} — {item['price']}₽\n"
    order_text += f"\n*Сумма: {total}₽*\n"
    order_text += "Менеджер свяжется с вами в ближайшее время!"

    await call.message.edit_text(
        text=order_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Сделать новый заказ", callback_data="menu")]
        ]),
        parse_mode="Markdown"
    )
    await call.answer("Заказ отправлен!")


@dp.callback_query(lambda c: c.data == "chat_mode")
async def enable_chat_mode(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = True

    await call.message.edit_text(
        "*AI-ПОМОЩНИК ВКЛЮЧЁН!*\n\n"
        "Теперь просто пиши, что хочешь:\n\n"
        "• Две пепперони и колу\n"
        "• Покажи корзину\n"
        "• Очисти всё\n"
        "• Что посоветуешь?\n\n"
        "Я всё пойму!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Вернуться в меню", callback_data="menu")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")],
            [InlineKeyboardButton(text="Выключить AI", callback_data="disable_ai")]
        ]),
        parse_mode="Markdown"
    )
    await call.answer("AI включён!")


@dp.callback_query(lambda c: c.data == "disable_ai")
async def disable_ai_mode(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = False

    await call.message.edit_text(
        "*AI-ПОМОЩНИК ВЫКЛЮЧЕН*\n\n"
        "Используй кнопки ниже",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")],
            [InlineKeyboardButton(text="AI-Помощник", callback_data="chat_mode")]
        ]),
        parse_mode="Markdown"
    )
    await call.answer()


@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if text in ALL_ITEMS:
        user_cart[user_id].append({"name": text, "price": ALL_ITEMS[text]})
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
                [InlineKeyboardButton(text="Меню", callback_data="menu")],
                [InlineKeyboardButton(text="Корзина", callback_data="cart")],
                [InlineKeyboardButton(text="Чат с AI", callback_data="chat_mode")]
            ])
        )
    else:
        await message.answer(
            "Не понял команду\n"
            "Нажми на кнопки или включи AI",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Меню", callback_data="menu")],
                [InlineKeyboardButton(text="AI-Помощник", callback_data="chat_mode")]
            ])
        )


async def main():
    print("Бот запущен — готов принимать заказы 24/7")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
