# bot.py — 1000% РАБОТАЕТ /start, проверено 21 ноября 2025
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer_photo(
        photo="https://i.ibb.co/m9kJ7B/welcome-burger.png",
        caption="Здарова, брат!\n\n*Burger King на максималках*\nПиши что хочешь — я всё сделаю!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")]
        ])
    )

@dp.callback_query(lambda c: c.data == "menu")
async def menu(call: types.CallbackQuery):
    await call.message.edit_caption(
        caption="*МЕНЮ*\nВоппер — 349₽\nКартошка — 149₽\nКола — 119₽",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ])
    )

@dp.callback_query(lambda c: c.data == "back")
async def back(call: types.CallbackQuery):
    await start(call.message)

@dp.message()
async def echo(message: types.Message):
    await message.answer("Пока просто тестовый бот, но скоро будет огонь!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
