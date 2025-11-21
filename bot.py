# bot.py — ВЕЧНЫЙ РАБОЧИЙ КОД (21 ноября 2025)
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Меню", callback_data="menu")],
        [InlineKeyboardButton(text="Корзина", callback_data="cart")]
    ])
    await message.answer_photo(
        photo="https://i.ibb.co/m9kJ7B/welcome-burger.png",
        caption=f"Здарова, {message.from_user.first_name}!\n\n*BURGER KING 2025 ЖИВОЙ НА 1000000%*",
        reply_markup=kb
    )

@dp.callback_query(lambda c: c.data in ["menu", "cart"])
async def buttons(call: types.CallbackQuery):
    if call.data == "menu":
        await call.message.edit_caption(caption="Твоё эпичное меню уже тут!\nСкоро всё будет работать на максималках!", reply_markup=call.message.reply_markup)
    else:
        await call.message.edit_caption(caption="Корзина работает!\nСкоро добавим заказы и оплату!", reply_markup=call.message.reply_markup)
    await call.answer()

async def main():
    print("Бот запущен и живой!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
