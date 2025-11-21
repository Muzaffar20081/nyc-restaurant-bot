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
        "Burger King бот ЖИВОЙ на 1000000%\n\n"
        "Твой самый крутой бот в России работает!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="m")],
            [InlineKeyboardButton(text="Корзина", callback_data="c")]
        ])
    )

@dp.callback_query(lambda c: c.data == "m")
async def menu(call: types.CallbackQuery):
    await call.message.edit_text("Твоё эпичное меню уже тут!\nСкоро всё будет красиво!", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="start")]]))
    await call.answer()

@dp.callback_query(lambda c: c.data == "c")
async def cart(call: types.CallbackQuery):
    await call.message.edit_text("Корзина работает!\nСкоро добавим все вкусняшки!", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="start")]]))
    await call.answer()

@dp.callback_query(lambda c: c.data == "start")
async def back(call: types.CallbackQuery):
    await start(call.message)

async def main():
    print("БОТ ЗАПУЩЕН — ЖИВОЙ НА 1000000%")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
