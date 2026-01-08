# minimal_bot.py - МИНИМАЛЬНЫЙ РАБОЧИЙ БОТ
import asyncio
import logging

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Импортируем aiogram
try:
    from aiogram import Bot, Dispatcher, types
    from aiogram.filters import CommandStart
    logger.info("✅ Aiogram импортирован успешно")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта aiogram: {e}")
    exit(1)

# ВАШ ТОКЕН БОТА
BOT_TOKEN = "8244967100:AAF67beMM450dqwz1q0DjnFJohkMl0qjXAE"

# Создаем бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logger.info("✅ Бот создан")

# ========== ПРОСТАЯ КОМАНДА /START ==========
@dp.message(CommandStart())
async def start_command(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} вызвал /start")
    
    # Простая текстовая клавиатура
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🍔 Бургеры")],
            [types.KeyboardButton(text="🍕 Пицца")],
            [types.KeyboardButton(text="🍣 Суши")],
            [types.KeyboardButton(text="🛒 Корзина")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"Я бот ресторана! Выберите категорию:",
        reply_markup=keyboard
    )

# ========== ОБРАБОТКА ТЕКСТА ==========
@dp.message()
async def handle_text(message: types.Message):
    text = message.text
    logger.info(f"Пользователь {message.from_user.id} написал: {text}")
    
    if text == "🍔 Бургеры":
        await message.answer(
            "🍔 <b>Наши бургеры:</b>\n\n"
            "1. Классический - 350₽\n"
            "2. Чизбургер - 450₽\n"
            "3. Веганский - 400₽\n\n"
            "Напишите номер бургера чтобы добавить в корзину.",
            parse_mode="HTML"
        )
    
    elif text == "🍕 Пицца":
        await message.answer(
            "🍕 <b>Наша пицца:</b>\n\n"
            "1. Маргарита - 550₽\n"
            "2. Пепперони - 650₽\n"
            "3. 4 Сыра - 600₽\n\n"
            "Напишите номер пиццы чтобы добавить в корзину.",
            parse_mode="HTML"
        )
    
    elif text == "🍣 Суши":
        await message.answer(
            "🍣 <b>Наши суши:</b>\n\n"
            "1. Филадельфия - 450₽\n"
            "2. Калифорния - 420₽\n"
            "3. Запеченные роллы - 480₽\n\n"
            "Напишите номер чтобы добавить в корзину.",
            parse_mode="HTML"
        )
    
    elif text == "🛒 Корзина":
        await message.answer(
            "🛒 <b>Ваша корзина:</b>\n\n"
            "Пока пусто. Добавьте товары из меню!",
            parse_mode="HTML"
        )
    
    elif text in ["1", "2", "3"]:
        await message.answer(
            f"✅ Товар {text} добавлен в корзину!\n"
            f"Используйте кнопки для продолжения."
        )
    
    else:
        await message.answer(
            "🤖 Я бот ресторана!\n"
            "Используйте кнопки ниже или команду /start"
        )

# ========== ЗАПУСК ==========
async def main():
    logger.info("=" * 50)
    logger.info("🚀 МИНИМАЛЬНЫЙ БОТ ЗАПУСКАЕТСЯ")
    logger.info("=" * 50)
    
    try:
        # Проверка токена
        bot_info = await bot.get_me()
        logger.info(f"🤖 Бот: @{bot_info.username}")
        logger.info(f"📛 Имя: {bot_info.first_name}")
        
        # Запуск
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ ОШИБКА: {type(e).__name__}: {e}")
        logger.error("Проверьте:")
        logger.error("1. Токен бота")
        logger.error("2. Интернет соединение")
        logger.error("3. Блокировку Telegram")

if __name__ == "__main__":
    asyncio.run(main())
