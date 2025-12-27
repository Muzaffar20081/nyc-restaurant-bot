# bot.py — ГЛАВНЫЙ ФАЙЛ (всё соединяет)
import asyncio
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from ai_brain import ask_ai

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

user_cart = defaultdict(list)

# Твои фото
PHOTOS = {
    "start": "https://i.ibb.co/m9kJ7B/welcome-burger.png",
    "menu": "https://i.ibb.co/m9kJ7B/welcome-burger.png",
    "cart": "https://i.ibb.co/m9kJ7B/welcome-burger.png"
}

# Пример меню (потом можно загружать из menus/)
MENU_TEXT = """
*МЕНЮ BURGER KING 2025*

Воппер — 349₽
Двойной Воппер — 449₽
Чизбургер — 149₽
Картошка — 149₽
Кола — 119₽
Наггетсы — 259₽
"""

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer_photo(
        photo=PHOTOS["start"],
        caption=f"Здарова, {message.from_user.first_name}!\n\n*BURGER KING 2025 ЖИВОЙ!*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ]),
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "menu")
async def show_menu(call: types.CallbackQuery):
    await call.message.edit_media(
        media=InputMediaPhoto(
            media=PHOTOS["menu"],
            caption=MENU_TEXT,
            parse_mode="Markdown"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Добавить Воппер", callback_data="add_Воппер")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_item(call: types.CallbackQuery):
    item = call.data[4:]
    prices = {"Воппер": 349, "Двойной Воппер": 449, "Чизбургер": 149}
    if item in prices:
        user_cart[call.from_user.id].append({"name": item, "price": prices[item]})
        await call.answer(f"{item} добавлен!")
    else:
        await call.answer("Товар не найден")

@dp.callback_query(lambda c: c.data == "cart")
async def cart(call: types.CallbackQuery):
    items = user_cart[call.from_user.id]
    if not items:
        caption = "*Корзина пустая!*"
    else:
        total = sum(i["price"] for i in items)
        caption = "*Корзина:*\n" + "\n".join([f"{i['name']} — {i['price']}₽" for i in items]) + f"\nИтого: {total}₽"
    await call.message.edit_caption(caption=caption, parse_mode="Markdown")
    await call.answer()

@dp.message()
async def text_handler(message: types.Message):
    if not message.text:
        return
    answer = await ask_ai(message.text)
    await message.answer(answer)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
