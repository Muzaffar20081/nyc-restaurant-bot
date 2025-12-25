# bot.py
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage  # или RedisStorage2 позже

# ── Импорты твоих модулей ───────────────────────────────
from config import config
from menus import MENU_BY_CUISINE
from ai_brain import *           # или конкретные функции
from database import *           # init_db, get_order и т.д.
from restaurants import *        # если есть

# ── Роутеры / хендлеры ──────────────────────────────────
dp = Dispatcher(storage=MemoryStorage())

# Здесь все твои обработчики (пока прямо в этом файле)
# ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓

@dp.message(commands=["start"])
async def cmd_start(message: types.Message, state: FSMContext):
    # твоя логика приветствия и выбора кухни
    pass

@dp.callback_query(lambda c: c.data.startswith("cuisine:"))
async def process_cuisine(callback: types.CallbackQuery, state: FSMContext):
    # выбор кухни
    pass

# ... остальные твои @dp.message, @dp.callback_query ...

# ── Запуск бота ─────────────────────────────────────────
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    
    bot = Bot(token=config.BOT_TOKEN)
    
    # Если нужно — инициализация БД
    # await init_database()
    
    await dp.start_polling(
        bot,
        allowed_updates=types.default_allowed_updates
    )

if __name__ == "__main__":
    asyncio.run(main())
