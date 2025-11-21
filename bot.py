# bot.py — САМЫЙ ПРОСТОЙ, НО 1000% РАБОЧИЙ
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        f"Здарова, {message.from_user.first_name}!\n\n"
        "Burger King бот живой на 1000%\n\n"
        "Го заказывать!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )

@dp.callback_query(lambda c: c.data == "menu")
async def menu(call: types.CallbackQuery):
    await call.message.edit_text("Тут будет твоё крутое меню!", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="start")]]))
    await call.answer()

@dp.callback_query(lambda c: c.data == "cart")
async def cart(call: types.CallbackQuery):
    await call.message.edit_text("Корзина пока пустая", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="start")]]))
    await call.answer()

@dp.callback_query(lambda c: c.data == "start")
async def back(call: types.CallbackQuery):
    await start(call.message)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
