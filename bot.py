import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN, CAFES, DEFAULT_CAFE

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище выбранных кафе
user_cafes = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start"""
    user_id = message.from_user.id
    user_cafes[user_id] = DEFAULT_CAFE
    
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🍽️ Меню")],
            [types.KeyboardButton(text="🏪 Сменить кафе")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"Я бот для заказа еды. Выберите действие:",
        reply_markup=keyboard
    )

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    """Показать меню"""
    user_id = message.from_user.id
    cafe_key = user_cafes.get(user_id, DEFAULT_CAFE)
    cafe_name = CAFES.get(cafe_key, {}).get("name", "Кафе")
    
    await message.answer(
        f"🍽️ *Меню {cafe_name}:*\n\n"
        f"1. Пицца Маргарита - 450₽\n"
        f"2. Пицца Пепперони - 550₽\n"
        f"3. Паста Карбонара - 380₽\n"
        f"4. Салат Цезарь - 280₽\n"
        f"5. Кола 0.5л - 150₽",
        parse_mode="Markdown"
    )

@dp.message(Command("cafe"))
async def cmd_cafe(message: types.Message):
    """Сменить кафе"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=cafe["name"], callback_data=f"cafe_{cafe_key}")]
        for cafe_key, cafe in CAFES.items()
    ])
    
    await message.answer("🏪 Выберите кафе:", reply_markup=keyboard)

@dp.callback_query(lambda call: call.data.startswith("cafe_"))
async def select_cafe(call: types.CallbackQuery):
    """Обработка выбора кафе"""
    cafe_key = call.data.replace("cafe_", "")
    cafe_name = CAFES.get(cafe_key, {}).get("name", "Кафе")
    
    user_cafes[call.from_user.id] = cafe_key
    
    await call.message.edit_text(f"✅ Выбрано: {cafe_name}")

@dp.message(lambda message: message.text == "🍽️ Меню")
async def menu_button(message: types.Message):
    """Кнопка Меню"""
    await cmd_menu(message)

@dp.message(lambda message: message.text == "🏪 Сменить кафе")
async def cafe_button(message: types.Message):
    """Кнопка Сменить кафе"""
    await cmd_cafe(message)

@dp.message()
async def echo(message: types.Message):
    """Ответ на любое сообщение"""
    await message.answer("Напишите /start для начала")

async def main():
    """Запуск бота"""
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
