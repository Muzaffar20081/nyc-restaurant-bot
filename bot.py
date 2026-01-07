# test_bot.py - АБСОЛЮТНО МИНИМАЛЬНЫЙ БОТ
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

# ЗАМЕНИТЕ НА ВАШ ТОКЕН
TOKEN = "8244967100:AAF67beMM450dqwz1q0DjnFJohkMl0qjXAE"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(f"Привет, {message.from_user.first_name}! Бот работает! ✅")

@dp.message()
async def echo(message: types.Message):
    await message.answer(f"Вы написали: {message.text}")

async def main():
    print("🚀 Тестовый бот запускается...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
