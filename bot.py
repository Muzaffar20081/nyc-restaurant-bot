import os
import importlib
import logging
import sys
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, CAFES, DEFAULT_CAFE
from ai_brain import ask_grok

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_cart = defaultdict(list)
ai_mode = defaultdict(bool)
user_cafe = defaultdict(lambda: DEFAULT_CAFE)

def load_menu(cafe_key):
    """Загружает меню для конкретного кафе"""
    try:
        logger.info(f"Загрузка меню для кафе: {cafe_key}")
        
        if cafe_key not in CAFES:
            logger.warning(f"Кафе {cafe_key} не найдено, используется {DEFAULT_CAFE}")
            cafe_key = DEFAULT_CAFE
        
        cafe_config = CAFES[cafe_key]
        module_name = cafe_config["menu_file"]
        
        logger.info(f"Импорт модуля: {module_name}")
        
        # Импортируем модуль меню
        if module_name == "menus.italian_menu":
            from menus import italian_menu
            return italian_menu.CATEGORIES, italian_menu.ALL_ITEMS, italian_menu.MENU_TEXT
        elif module_name == "menus.sushi_menu":
            from menus import sushi_menu
            return sushi_menu.CATEGORIES, sushi_menu.ALL_ITEMS, sushi_menu.MENU_TEXT
        elif module_name == "menus.burger_menu":
            from menus import burger_menu
            return burger_menu.CATEGORIES, burger_menu.ALL_ITEMS, burger_menu.MENU_TEXT
        else:
            # Пробуем динамический импорт
            menu_module = importlib.import_module(module_name)
            return menu_module.CATEGORIES, menu_module.ALL_ITEMS, menu_module.MENU_TEXT
            
    except ImportError as e:
        logger.error(f"Ошибка импорта меню для {cafe_key}: {e}")
        
        # Возвращаем простые тестовые данные
        if cafe_key == "italy":
            CATEGORIES = {
                "🍕 Пицца": {"Маргарита": 450, "Пепперони": 550},
                "🍝 Паста": {"Карбонара": 400, "Болоньезе": 450}
            }
            ALL_ITEMS = {"Маргарита": 450, "Пепперони": 550, "Карбонара": 400, "Болоньезе": 450}
            MENU_TEXT = "🍕 *Итальянская кухня* - тестовое меню"
        elif cafe_key == "sushi":
            CATEGORIES = {
                "🍣 Роллы": {"Филадельфия": 450, "Калифорния": 400},
                "🍱 Сеты": {"Сет на 2 персоны": 1200}
            }
            ALL_ITEMS = {"Филадельфия": 450, "Калифорния": 400, "Сет на 2 персоны": 1200}
            MENU_TEXT = "🍣 *Суши-бар* - тестовое меню"
        elif cafe_key == "burger":
            CATEGORIES = {
                "🍔 Бургеры": {"Чизбургер": 300, "Чикенбургер": 350},
                "🍟 Закуски": {"Картофель фри": 150}
            }
            ALL_ITEMS = {"Чизбургер": 300, "Чикенбургер": 350, "Картофель фри": 150}
            MENU_TEXT = "🍔 *Бургер-хаус* - тестовое меню"
        else:
            CATEGORIES = {}
            ALL_ITEMS = {}
            MENU_TEXT = "📋 Меню временно недоступно"
        
        return CATEGORIES, ALL_ITEMS, MENU_TEXT
    except Exception as e:
        logger.error(f"Ошибка загрузки меню для {cafe_key}: {e}")
        return {}, {}, "📋 Меню временно недоступно"

@dp.message(CommandStart())
async def start(message: types.Message):
    """Обработчик команды /start"""
    try:
        user_id = message.from_user.id
        ai_mode[user_id] = False
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍝 Итальянское кафе", callback_data="cafe_italy")],
            [InlineKeyboardButton(text="🍣 Суши-бар", callback_data="cafe_sushi")],
            [InlineKeyboardButton(text="🍔 Бургер-хаус", callback_data="cafe_burger")],
        ])
        
        welcome_text = """
🎊 *ДОБРО ПОЖАЛОВАТЬ В МИР ВКУСА!* 🎊

🌟 *Выберите кухню вашей мечты:*

• 🍝 *Италия* - нежная паста и ароматная пицца
• 🍣 *Япония* - изысканные суши и роллы  
• 🍔 *Америка* - сочные бургеры и хрустящий картофель

🎯 *Готовы к гастрономическому путешествию?*
"""
        
        await message.answer(
            welcome_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        logger.info(f"Пользователь {user_id} запустил бота")
        
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")
        await message.answer("Произошла ошибка при запуске бота. Попробуйте позже.")

@dp.callback_query(lambda c: c.data.startswith("cafe_"))
async def select_cafe(call: types.CallbackQuery):
    """Выбор кафе"""
    try:
        user_id = call.from_user.id
        cafe_key = call.data[5:]  # Убираем "cafe_"
        
        logger.info(f"Пользователь {user_id} выбирает кафе: {cafe_key}")
        
        if cafe_key in CAFES:
            user_cafe[user_id] = cafe_key
            cafe_name = CAFES[cafe_key]["name"]
            cafe_photo = CAFES[cafe_key].get("photo", "")
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📖 Открыть меню", callback_data="menu")],
                [InlineKeyboardButton(text="🛒 Моя корзина", callback_data="cart")],
                [InlineKeyboardButton(text="✨ AI-Помощник", callback_data="chat_mode")],
                [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
            ])
            
            # Проверяем, загружается ли меню
            try:
                CATEGORIES, ALL_ITEMS, MENU_TEXT = load_menu(cafe_key)
                logger.info(f"Меню {cafe_key} загружено: {len(CATEGORIES)} категорий")
            except Exception as e:
                logger.error(f"Ошибка проверки меню: {e}")
            
            welcome_message = f"""
🏪 *{cafe_name}*

🎉 *Добро пожаловать в мир изысканных вкусов!*

🍽️ *Готовы открыть для себя новые гастрономические горизонты?*

💫 *Выбирайте удобный способ заказа:*
"""
            
            try:
                if cafe_photo:
                    await bot.send_photo(
                        chat_id=call.message.chat.id,
                        photo=cafe_photo,
                        caption=welcome_message,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                    await call.message.delete()
                else:
                    await call.message.edit_text(
                        welcome_message,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.warning(f"Не удалось отредактировать сообщение: {e}")
                await call.message.answer(
                    welcome_message,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            
            logger.info(f"Пользователь {user_id} выбрал кафе: {cafe_name}")
        else:
            await call.answer("❌ Кафе не найдено")
            logger.warning(f"Кафе {cafe_key} не найдено для пользователя {user_id}")
        
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в select_cafe: {e}")
        await call.answer("❌ Произошла ошибка при выборе кафе")

@dp.callback_query(lambda c: c.data == "menu")
async def show_categories(call: types.CallbackQuery):
    """Показать категории меню"""
    try:
        user_id = call.from_user.id
        ai_mode[user_id] = False
        
        cafe_key = user_cafe[user_id]
        CATEGORIES, ALL_ITEMS, MENU_TEXT = load_menu(cafe_key)
        cafe_name = CAFES[cafe_key]["name"]
        
        logger.info(f"Показ категорий для {cafe_name}, категорий: {len(CATEGORIES)}")
        
        if not CATEGORIES:
            await call.answer("⚠️ Меню пустое или недоступно")
            # Показываем сообщение с ошибкой
            error_text = f"""
🏪 *{cafe_name}*

⚠️ *Меню временно недоступно*

Пожалуйста, выберите другое кафе или попробуйте позже.
"""
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")],
                [InlineKeyboardButton(text="🛒 Моя корзина", callback_data="cart")]
            ])
            await call.message.edit_text(
                text=error_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        
        keyboard = []
        for category_name in CATEGORIES.keys():
            # Упрощаем создание callback_data
            clean_name = category_name.replace('🍕', '').replace('🍝', '').replace('🥗', '').replace('🍹', '').replace('🍣', '').replace('🍱', '').replace('🍤', '').replace('🍵', '').replace('🍔', '').replace('🍟', '').replace('🥤', '').replace('🍦', '').strip()
            callback_data = f"category_{clean_name.replace(' ', '_')}"
            keyboard.append([InlineKeyboardButton(
                text=f"🎯 {category_name}", 
                callback_data=callback_data
            )])
        
        keyboard += [
            [InlineKeyboardButton(text="🛒 Посмотреть корзину", callback_data="cart")],
            [InlineKeyboardButton(text="✨ AI-Помощник", callback_data="chat_mode")],
            [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
        ]
        
        await call.message.edit_text(
            text=f"🏪 *{cafe_name}*\n\n{MENU_TEXT}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await call.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_categories: {e}")
        await call.answer("❌ Ошибка при загрузке меню")

# ... остальные функции остаются такими же как в предыдущем коде ...

async def main():
    """Основная функция запуска бота"""
    try:
        print("=" * 50)
        print("🎊 БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ! 🍽️")
        print("✨ Красивое меню активировано!")
        print("🤖 AI-помощник готов помочь!")
        print(f"📊 Доступные кафе: {', '.join(CAFES.keys())}")
        print("=" * 50)
        
        # Проверяем наличие файлов меню
        print("🔍 Проверка файлов меню...")
        for cafe_key, cafe_info in CAFES.items():
            module_name = cafe_info["menu_file"]
            print(f"  {cafe_key}: {module_name}")
            try:
                importlib.import_module(module_name)
                print(f"    ✅ Успешно загружено")
            except Exception as e:
                print(f"    ❌ Ошибка: {e}")
        
        logger.info("Бот запущен успешно")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        print(f"❌ Критическая ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
