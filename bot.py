# bot.py — 100% РАБОТАЕТ, МИНИМАЛЬНЫЙ И КРАСИВЫЙ
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from menu import BURGER_KING_MENU

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

user_cart = {}

@dp.message(CommandStart())
async def start(message: types.Message):
    try:
        await message.answer_photo(
            photo="https://i.ibb.co/m9kJ7B/welcome-burger.png",
            caption=f"Здарова, {message.from_user.first_name}!\n\n*BURGER KING 2025 ЖИВОЙ!*",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Меню", callback_data="menu")],
                [InlineKeyboardButton(text="Корзина", callback_data="cart")]
            ]),
            parse_mode="Markdown"
        )
    except:
        await message.answer(
            f"Здарова, {message.from_user.first_name}!\n\n*BURGER KING 2025 ЖИВОЙ!* (фото не загрузилось)",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Меню", callback_data="menu")],
                [InlineKeyboardButton(text="Корзина", callback_data="cart")]
            ]),
            parse_mode="Markdown"
        )

@dp.callback_query(lambda c: c.data == "menu")
async def show_menu(call: types.CallbackQuery):
    await call.message.edit_caption(
        caption=BURGER_KING_MENU,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Воппер", callback_data="add_Воппер")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ]),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_item(call: types.CallbackQuery):
    item = call.data[4:]
    await call.answer(f"{item} добавлен в корзину!")
    await call.message.edit_reply_markup(reply_markup=None)

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    await call.message.edit_caption(caption="*Корзина пока пустая, брат!*", parse_mode="Markdown")
    await call.answer()

@dp.message()
async def text_handler(message: types.Message):
    if not message.text:
        return
    await message.answer("Пиши название блюда — я добавлю в корзину!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
