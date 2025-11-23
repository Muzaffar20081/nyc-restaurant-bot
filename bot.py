# bot.py — ПРОСТО РАБОТАЕТ НА 1000000%
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

bot = Bot(token=os.environ.get("BOT_TOKEN"))
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        f"ЗДАРОВА, {message.from_user.first_name}!\n\n"
        "БОТ ЖИВОЙ НА 1000000%\n\n"
        "Burger King 2025 работает!\n"
        "Скоро будет всё — меню, корзина, оплата!"
    )

async def main():
    print("БОТ ЗАПУЩЕН И ЖИВОЙ!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
