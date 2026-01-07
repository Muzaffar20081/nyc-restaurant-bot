# simple_bot.py - САМЫЙ ПРОСТОЙ РАБОЧИЙ БОТ
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ВАШ ТОКЕН - скопируйте из @BotFather
BOT_TOKEN = "8244967100:AAF67beMM450dqwz1q0DjnFJohkMl0qjXAE"

# Создаем бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Простая корзина в памяти
user_carts = {}

# Простое меню
simple_menu = {
    "🍔 Бургеры": [
        {"name": "Классический бургер", "price": 350},
        {"name": "Чизбургер", "price": 450},
        {"name": "Веганский бургер", "price": 400},
    ],
    "🍕 Пицца": [
        {"name": "Маргарита", "price": 550},
        {"name": "Пепперони", "price": 650},
        {"name": "4 Сыра", "price": 600},
    ],
    "🍣 Суши": [
        {"name": "Филадельфия", "price": 450},
        {"name": "Калифорния", "price": 420},
        {"name": "Запеченные роллы", "price": 480},
    ]
}

# ========== КОМАНДА START ==========
@dp.message(CommandStart())
async def start_command(message: types.Message):
    user = message.from_user
    logger.info(f"Пользователь {user.id} запустил бота")
    
    # Создаем кнопки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Бургеры", callback_data="category:burgers")],
        [InlineKeyboardButton(text="🍕 Пицца", callback_data="category:pizza")],
        [InlineKeyboardButton(text="🍣 Суши", callback_data="category:sushi")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart")]
    ])
    
    await message.answer(
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"Добро пожаловать в наш ресторан!\n"
        f"Выберите категорию:",
        parse_mode="HTML",
        reply_markup=keyboard
    )

# ========== ПОКАЗАТЬ КАТЕГОРИЮ ==========
@dp.callback_query(lambda c: c.data.startswith("category:"))
async def show_category(callback: types.CallbackQuery):
    category = callback.data.split(":")[1]
    
    if category == "burgers":
        items = simple_menu["🍔 Бургеры"]
        cat_name = "🍔 Бургеры"
    elif category == "pizza":
        items = simple_menu["🍕 Пицца"]
        cat_name = "🍕 Пицца"
    elif category == "sushi":
        items = simple_menu["🍣 Суши"]
        cat_name = "🍣 Суши"
    else:
        await callback.answer("Категория не найдена")
        return
    
    # Создаем кнопки для товаров
    buttons = []
    for item in items:
        buttons.append([
            InlineKeyboardButton(
                text=f"{item['name']} - {item['price']}₽",
                callback_data=f"item:{category}:{item['name']}"
            )
        ])
    
    # Добавляем кнопку назад
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(
        f"<b>{cat_name}</b>\n\nВыберите блюдо:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

# ========== ПОКАЗАТЬ ТОВАР ==========
@dp.callback_query(lambda c: c.data.startswith("item:"))
async def show_item(callback: types.CallbackQuery):
    try:
        _, category, item_name = callback.data.split(":", 2)
        
        # Находим товар
        if category == "burgers":
            items_list = simple_menu["🍔 Бургеры"]
        elif category == "pizza":
            items_list = simple_menu["🍕 Пицца"]
        elif category == "sushi":
            items_list = simple_menu["🍣 Суши"]
        else:
            await callback.answer("Ошибка")
            return
        
        item = None
        for i in items_list:
            if i['name'] == item_name:
                item = i
                break
        
        if not item:
            await callback.answer("Товар не найден")
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить в корзину", callback_data=f"add:{category}:{item_name}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data=f"category:{category}")]
        ])
        
        await callback.message.edit_text(
            f"<b>{item['name']}</b>\n\n"
            f"Цена: <b>{item['price']}₽</b>\n\n"
            f"Добавить в корзину?",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_item: {e}")
        await callback.answer("Ошибка")

# ========== ДОБАВИТЬ В КОРЗИНУ ==========
@dp.callback_query(lambda c: c.data.startswith("add:"))
async def add_to_cart(callback: types.CallbackQuery):
    try:
        _, category, item_name = callback.data.split(":", 2)
        
        # Находим товар
        if category == "burgers":
            items_list = simple_menu["🍔 Бургеры"]
        elif category == "pizza":
            items_list = simple_menu["🍕 Пицца"]
        elif category == "sushi":
            items_list = simple_menu["🍣 Суши"]
        else:
            await callback.answer("Ошибка")
            return
        
        item = None
        for i in items_list:
            if i['name'] == item_name:
                item = i
                break
        
        if not item:
            await callback.answer("Товар не найден")
            return
        
        user_id = callback.from_user.id
        
        # Инициализируем корзину
        if user_id not in user_carts:
            user_carts[user_id] = []
        
        # Добавляем товар
        user_carts[user_id].append({
            "name": item['name'],
            "price": item['price'],
            "quantity": 1
        })
        
        await callback.answer(f"✅ {item['name']} добавлен!")
        
        # Возвращаемся в категорию
        await show_category(callback)
        
    except Exception as e:
        logger.error(f"Ошибка в add_to_cart: {e}")
        await callback.answer("Ошибка при добавлении")

# ========== ПОКАЗАТЬ КОРЗИНУ ==========
@dp.callback_query(lambda c: c.data == "show_cart")
async def show_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cart = user_carts.get(user_id, [])
    
    if not cart:
        text = "🛒 <b>Ваша корзина пуста</b>\n\nДобавьте товары из меню!"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍽️ К меню", callback_data="back_to_main")]
        ])
    else:
        text = "🛒 <b>Ваша корзина:</b>\n\n"
        total = 0
        
        for i, item in enumerate(cart, 1):
            item_total = item['price'] * item['quantity']
            text += f"{i}. {item['name']}\n"
            text += f"   {item['price']}₽ × {item['quantity']} = {item_total}₽\n\n"
            total += item_total
        
        text += f"💵 <b>Итого: {total}₽</b>"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="make_order")],
            [InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="◀️ Продолжить покупки", callback_data="back_to_main")]
        ])
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

# ========== ОФОРМИТЬ ЗАКАЗ ==========
@dp.callback_query(lambda c: c.data == "make_order")
async def make_order(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cart = user_carts.get(user_id, [])
    
    if not cart:
        await callback.answer("Корзина пуста")
        return
    
    # Рассчитываем сумму
    total = sum(item['price'] * item['quantity'] for item in cart)
    
    # Формируем детали заказа
    order_details = "✅ <b>Заказ оформлен!</b>\n\n"
    order_details += "<b>Ваш заказ:</b>\n"
    
    for item in cart:
        order_details += f"• {item['name']} - {item['price']}₽\n"
    
    order_details += f"\n<b>Итого: {total}₽</b>\n\n"
    order_details += "Спасибо за заказ! Ожидайте звонка оператора."
    
    # Очищаем корзину
    if user_id in user_carts:
        user_carts[user_id] = []
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍽️ Новый заказ", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        order_details,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer("✅ Заказ принят!")

# ========== ОЧИСТИТЬ КОРЗИНУ ==========
@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in user_carts:
        user_carts[user_id] = []
    
    await callback.answer("Корзина очищена")
    await show_cart(callback)

# ========== НАЗАД НА ГЛАВНУЮ ==========
@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    user = callback.from_user
    
    # Считаем товары в корзине
    cart_count = len(user_carts.get(user.id, []))
    cart_text = f" ({cart_count})" if cart_count > 0 else ""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍔 Бургеры", callback_data="category:burgers")],
        [InlineKeyboardButton(text="🍕 Пицца", callback_data="category:pizza")],
        [InlineKeyboardButton(text="🍣 Суши", callback_data="category:sushi")],
        [InlineKeyboardButton(text=f"🛒 Корзина{cart_text}", callback_data="show_cart")]
    ])
    
    await callback.message.edit_text(
        f"👋 <b>{user.first_name}</b>, выберите категорию:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

# ========== ОБРАБОТКА ВСЕХ СООБЩЕНИЙ ==========
@dp.message()
async def handle_all_messages(message: types.Message):
    if message.text and not message.text.startswith('/'):
        await message.answer(
            "🤖 Я бот для заказа еды!\n\n"
            "Используйте кнопки меню или команду:\n"
            "/start - Начать заказ"
        )

# ========== ЗАПУСК БОТА ==========
async def main():
    print("=" * 50)
    print("🚀 ПРОСТОЙ БОТ ЗАПУСКАЕТСЯ...")
    print(f"🤖 Токен: {BOT_TOKEN[:10]}...")
    print("=" * 50)
    print("📱 Откройте Telegram и найдите бота")
    print("💬 Напишите /start")
    print("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
