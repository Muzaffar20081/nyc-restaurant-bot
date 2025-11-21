import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("ЖИВОЙ, БРАТ!\n\n/start работает на 1000000%\n\nТвой бот живой!")

async def main():
    print("БОТ ЗАПУЩЕН")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
