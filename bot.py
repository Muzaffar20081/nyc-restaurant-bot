# bot.py — МИНИМАЛЬНЫЙ, НО 1000% РАБОЧИЙ
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("ЗДАРОВА, БРАТИШКА!\n\n/start РАБОТАЕТ НА 1000%\n\nСкоро будет самый крутой Burger King в России!")

async def main():
    print("Бот запущен и ждёт команды...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())