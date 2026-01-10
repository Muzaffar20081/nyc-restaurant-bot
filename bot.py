# bot.py - УЛУЧШЕННАЯ ВЕРСИЯ
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List

# Загружаем токен из config.py
try:
    from config import BOT_TOKEN
    print(f"✅ Токен загружен: {BOT_TOKEN[:10]}...")
except ImportError:
    print("❌ Ошибка: Создайте файл config.py с BOT_TOKEN")
    exit(1)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище данных (временное, лучше заменить на БД)
carts: Dict[int, List[dict]] = {}

# Меню с категориями (соответствует файлам из image.png)
menu_categories = {
    "burgers": [
        {"id": "burger_classic", "name": "🍔 Классический бургер", "price": 350},
        {"id": "burger_cheese", "name": "🍔 Чизбургер", "price": 400},
        {"id": "burger_bacon", "name": "🍔 Бекон бургер", "price": 450},
    ],
    "italian": [
        {"id": "pizza_margarita", "name": "🍕 Маргарита", "price": 550},
        {"id": "pizza_pepperoni", "name": "🍕 Пепперони", "price": 600},
        {"id": "pasta_carbonara", "name": "🍝 Карбонара", "price": 400},
    ],
    "sushi": [
        {"id": "sushi_philadelphia", "name": "🍣 Филадельфия", "price": 450},
        {"id": "sushi_california", "name": "🍣 Калифорния", "price": 480},
        {"id": "sushi_set", "name": "🍱 Сет суши", "price": 850},
    ]
}

# Функция для создания клавиатуры меню
def create_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру с меню"""
    keyboard_buttons = [
        [InlineKeyboardButton(text="🍔 Бургеры", callback_data="category_burgers")],
        [InlineKeyboardButton(text="🍕 Итальянская кухня", callback_data="category_italian")],
        [InlineKeyboardButton(text="🍣 Суши", callback_data="category_sushi")],
    ]
    
    # Кнопка корзины с количеством
    cart_count = len(carts.get(user_id, []))
    cart_text = f"🛒 Корзина ({cart_count})" if cart_count > 0 else "🛒 Корзина"
    
    keyboard_buttons.append([
        InlineKeyboardButton(text=cart_text, callback_data="show_cart"),
        InlineKeyboardButton(text="❓ Помощь", callback_data="help")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

# Функция для создания клавиатуры категории
def create_category_keyboard(category: str, user_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбранной категории"""
    items = menu_categories.get(category, [])
    
    keyboard_buttons = []
    for item in items:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{item['name']} - {item['price']}₽",
                callback_data=f"add_{item['id']}"
            )
        ])
    
    cart_count = len(carts.get(user_id, []))
    cart_text = f"🛒 Корзина ({cart_count})" if cart_count > 0 else "🛒 Корзина"
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu"),
        InlineKeyboardButton(text=cart_text, callback_data="show_cart")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

# ========== КОМАНДЫ ==========
@dp.message(CommandStart())
async def start_command(message: types.Message):
    user = message.from_user
    welcome_text = f"""
👋 <b>Привет, {user.first_name}!</b>

Добро пожаловать в наш ресторан!
Выберите категорию блюд:
"""
    
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=create_menu_keyboard(user.id)
    )

@dp.message(Command("menu"))
async def menu_command(message: types.Message):
    await message.answer(
        "🍽️ <b>Выберите категорию:</b>",
        parse_mode="HTML",
        reply_markup=create_menu_keyboard(message.from_user.id)
    )

# ========== КАТЕГОРИИ ==========
@dp.callback_query(lambda c: c.data.startswith("category_"))
async def show_category(callback: types.CallbackQuery):
    category = callback.data.replace("category_", "")
    category_names = {
        "burgers": "🍔 Бургеры",
        "italian": "🍕 Итальянская кухня",
        "sushi": "🍣 Суши"
    }
    
    await callback.message.edit_text(
        f"<b>{category_names.get(category, 'Меню')}:</b>\nВыберите блюдо:",
        parse_mode="HTML",
        reply_markup=create_category_keyboard(category, callback.from_user.id)
    )
    await callback.answer()

# ========== ДОБАВЛЕНИЕ В КОРЗИНУ ==========
@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(callback: types.CallbackQuery):
    item_id = callback.data.replace("add_", "")
    
    # Ищем товар во всех категориях
    item = None
    category_name = ""
    for category, items in menu_categories.items():
        for menu_item in items:
            if menu_item["id"] == item_id:
                item = menu_item
                category_name = category
                break
        if item:
            break
    
    if not item:
        await callback.answer("❌ Товар не найден")
        return
    
    user_id = callback.from_user.id
    
    # Инициализируем корзину
    if user_id not in carts:
        carts[user_id] = []
    
    # Добавляем товар
    carts[user_id].append({
        "name": item["name"],
        "price": item["price"],
        "id": item["id"]
    })
    
    await callback.answer(f"✅ {item['name']} добавлен в корзину!")
    
    # Возвращаемся к той же категории
    await callback.message.edit_reply_markup(
        reply_markup=create_category_keyboard(category_name, user_id)
    )

# ========== ПОКАЗ КОРЗИНЫ (остается без изменений) ==========
@dp.callback_query(lambda c: c.data == "show_cart")
async def show_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_cart = carts.get(user_id, [])
    
    if not user_cart:
        text = "🛒 <b>Ваша корзина пуста</b>\n\nДобавьте товары из меню!"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ К меню", callback_data="back_to_menu")]
        ])
    else:
        total = sum(item["price"] for item in user_cart)
        
        text = "🛒 <b>Ваша корзина:</b>\n\n"
        for i, item in enumerate(user_cart, 1):
            text += f"{i}. {item['name']} - {item['price']}₽\n"
        
        text += f"\n💰 <b>Итого: {total}₽</b>"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="⬅️ К меню", callback_data="back_to_menu")]
        ])
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()

# ========== ВОЗВРАТ В ГЛАВНОЕ МЕНЮ ==========
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🍽️ <b>Выберите категорию:</b>",
        parse_mode="HTML",
        reply_markup=create_menu_keyboard(callback.from_user.id)
    )
    await callback.answer()

# ========== ОСТАЛЬНЫЕ ФУНКЦИИ (без изменений) ==========
@dp.callback_query(lambda c: c.data == "checkout")
async def checkout(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_cart = carts.get(user_id, [])
    
    if not user_cart:
        await callback.answer("❌ Корзина пуста")
        return
    
    total = sum(item["price"] for item in user_cart)
    
    order_text = "✅ <b>Заказ оформлен!</b>\n\n"
    order_text += "<b>Ваш заказ:</b>\n"
    
    for item in user_cart:
        order_text += f"• {item['name']} - {item['price']}₽\n"
    
    order_text += f"\n💰 <b>Общая сумма: {total}₽</b>\n\n"
    order_text += "Спасибо за заказ! Ожидайте звонка оператора."
    
    carts[user_id] = []
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Новый заказ", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(order_text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer("✅ Заказ принят!")

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in carts:
        carts[user_id] = []
    
    await callback.answer("🗑️ Корзина очищена")
    await show_cart(callback)

@dp.callback_query(lambda c: c.data == "help")
async def help_command(callback: types.CallbackQuery):
    help_text = """
🤖 <b>Помощь по боту:</b>

<b>Как сделать заказ:</b>
1. Выберите категорию меню
2. Добавьте блюда в корзину
3. Перейдите в корзину
4. Оформите заказ

<b>Команды:</b>
/start - Начать заказ
/menu - Показать меню

<b>Поддержка:</b>
По вопросам пишите: @support
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(help_text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()

# ========== ЗАПУСК ==========
async def main():
    print("=" * 50)
    print("🚀 РЕСТОРАННЫЙ БОТ ЗАПУСКАЕТСЯ")
    print("=" * 50)
    print("📱 Откройте Telegram")
    print("🔍 Найдите своего бота")
    print("💬 Напишите /start")
    print("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
