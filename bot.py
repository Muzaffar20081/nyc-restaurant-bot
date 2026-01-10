# bot.py - НОВЫЙ КОД С НУЛЯ
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Загружаем токен из config.py
try:
    from config import BOT_TOKEN
    print(f"✅ Токен загружен: {BOT_TOKEN[:10]}...")
except ImportError:
    print("❌ Ошибка: Создайте файл config.py с BOT_TOKEN")
    exit(1)

# Создаем бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Корзина пользователей
carts = {}

# Меню блюд
menu_items = [
    {"id": "burger", "name": "🍔 Бургер", "price": 350},
    {"id": "pizza", "name": "🍕 Пицца", "price": 550},
    {"id": "sushi", "name": "🍣 Суши", "price": 450},
    {"id": "pasta", "name": "🍝 Паста", "price": 400},
    {"id": "salad", "name": "🥗 Салат", "price": 300},
    {"id": "drink", "name": "🥤 Напиток", "price": 150},
]

# ========== КОМАНДА START ==========
@dp.message(CommandStart())
async def start_command(message: types.Message):
    user = message.from_user
    
    # Создаем кнопки
    keyboard_buttons = []
    
    # Добавляем кнопки меню (по 2 в ряд)
    for i in range(0, len(menu_items), 2):
        row = []
        if i < len(menu_items):
            item1 = menu_items[i]
            row.append(InlineKeyboardButton(
                text=f"{item1['name']} - {item1['price']}₽",
                callback_data=f"add_{item1['id']}"
            ))
        if i + 1 < len(menu_items):
            item2 = menu_items[i + 1]
            row.append(InlineKeyboardButton(
                text=f"{item2['name']} - {item2['price']}₽",
                callback_data=f"add_{item2['id']}"
            ))
        keyboard_buttons.append(row)
    
    # Добавляем кнопку корзины
    user_id = message.from_user.id
    cart_count = len(carts.get(user_id, []))
    cart_text = f"🛒 Корзина ({cart_count})" if cart_count > 0 else "🛒 Корзина"
    
    keyboard_buttons.append([
        InlineKeyboardButton(text=cart_text, callback_data="show_cart"),
        InlineKeyboardButton(text="❓ Помощь", callback_data="help")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"Добро пожаловать в наш ресторан!\n"
        f"Выберите блюдо для заказа:",
        parse_mode="HTML",
        reply_markup=keyboard
    )

# ========== ДОБАВЛЕНИЕ В КОРЗИНУ ==========
@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(callback: types.CallbackQuery):
    item_id = callback.data.replace("add_", "")
    
    # Находим товар
    item = None
    for menu_item in menu_items:
        if menu_item["id"] == item_id:
            item = menu_item
            break
    
    if not item:
        await callback.answer("❌ Товар не найден")
        return
    
    user_id = callback.from_user.id
    
    # Создаем корзину если нет
    if user_id not in carts:
        carts[user_id] = []
    
    # Добавляем товар
    carts[user_id].append({
        "name": item["name"],
        "price": item["price"],
        "id": item["id"]
    })
    
    # Обновляем клавиатуру
    cart_count = len(carts[user_id])
    
    keyboard_buttons = []
    for i in range(0, len(menu_items), 2):
        row = []
        if i < len(menu_items):
            item1 = menu_items[i]
            row.append(InlineKeyboardButton(
                text=f"{item1['name']} - {item1['price']}₽",
                callback_data=f"add_{item1['id']}"
            ))
        if i + 1 < len(menu_items):
            item2 = menu_items[i + 1]
            row.append(InlineKeyboardButton(
                text=f"{item2['name']} - {item2['price']}₽",
                callback_data=f"add_{item2['id']}"
            ))
        keyboard_buttons.append(row)
    
    cart_text = f"🛒 Корзина ({cart_count})"
    keyboard_buttons.append([
        InlineKeyboardButton(text=cart_text, callback_data="show_cart"),
        InlineKeyboardButton(text="❓ Помощь", callback_data="help")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        f"✅ <b>{item['name']} добавлен в корзину!</b>\n\n"
        f"Цена: {item['price']}₽\n"
        f"Товаров в корзине: {cart_count}\n\n"
        f"Продолжайте выбирать:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    await callback.answer(f"✅ {item['name']} добавлен!")

# ========== ПОКАЗ КОРЗИНЫ ==========
@dp.callback_query(lambda c: c.data == "show_cart")
async def show_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_cart = carts.get(user_id, [])
    
    if not user_cart:
        text = "🛒 <b>Ваша корзина пуста</b>\n\nДобавьте товары из меню!"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад к меню", callback_data="back_to_menu")]
        ])
    else:
        # Считаем сумму
        total = sum(item["price"] for item in user_cart)
        
        # Формируем текст
        text = "🛒 <b>Ваша корзина:</b>\n\n"
        for i, item in enumerate(user_cart, 1):
            text += f"{i}. {item['name']} - {item['price']}₽\n"
        
        text += f"\n💰 <b>Итого: {total}₽</b>"
        
        # Кнопки
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="⬅️ Назад к меню", callback_data="back_to_menu")]
        ])
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

# ========== ОФОРМЛЕНИЕ ЗАКАЗА ==========
@dp.callback_query(lambda c: c.data == "checkout")
async def checkout(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_cart = carts.get(user_id, [])
    
    if not user_cart:
        await callback.answer("❌ Корзина пуста")
        return
    
    # Считаем сумму
    total = sum(item["price"] for item in user_cart)
    
    # Формируем заказ
    order_text = "✅ <b>Заказ оформлен!</b>\n\n"
    order_text += "<b>Ваш заказ:</b>\n"
    
    for item in user_cart:
        order_text += f"• {item['name']} - {item['price']}₽\n"
    
    order_text += f"\n💰 <b>Общая сумма: {total}₽</b>\n\n"
    order_text += "Спасибо за заказ! Ожидайте звонка оператора."
    
    # Очищаем корзину
    carts[user_id] = []
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Новый заказ", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(
        order_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer("✅ Заказ принят!")

# ========== ОЧИСТКА КОРЗИНЫ ==========
@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in carts:
        carts[user_id] = []
    
    await show_cart(callback)
    await callback.answer("🗑️ Корзина очищена")

# ========== ВОЗВРАТ В МЕНЮ ==========
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cart_count = len(carts.get(user_id, []))
    
    # Создаем кнопки
    keyboard_buttons = []
    for i in range(0, len(menu_items), 2):
        row = []
        if i < len(menu_items):
            item1 = menu_items[i]
            row.append(InlineKeyboardButton(
                text=f"{item1['name']} - {item1['price']}₽",
                callback_data=f"add_{item1['id']}"
            ))
        if i + 1 < len(menu_items):
            item2 = menu_items[i + 1]
            row.append(InlineKeyboardButton(
                text=f"{item2['name']} - {item2['price']}₽",
                callback_data=f"add_{item2['id']}"
            ))
        keyboard_buttons.append(row)
    
    cart_text = f"🛒 Корзина ({cart_count})" if cart_count > 0 else "🛒 Корзина"
    keyboard_buttons.append([
        InlineKeyboardButton(text=cart_text, callback_data="show_cart"),
        InlineKeyboardButton(text="❓ Помощь", callback_data="help")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        "🍽️ <b>Выберите блюдо для заказа:</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

# ========== ПОМОЩЬ ==========
@dp.callback_query(lambda c: c.data == "help")
async def help_command(callback: types.CallbackQuery):
    help_text = """
🤖 <b>Помощь по боту:</b>

<b>Как сделать заказ:</b>
1. Выберите блюдо из меню
2. Добавьте его в корзину
3. Перейдите в корзину
4. Оформите заказ

<b>Команды:</b>
/start - Начать заказ

<b>Кнопки:</b>
• 🍔 Блюда - выбрать еду
• 🛒 Корзина - просмотр заказа
• ✅ Оформить - завершить заказ
• 🗑️ Очистить - удалить всё

<b>Поддержка:</b>
По вопросам пишите: @support
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(
        help_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

# ========== ОБРАБОТКА СООБЩЕНИЙ ==========
@dp.message()
async def handle_messages(message: types.Message):
    if message.text == "/start":
        await start_command(message)
    else:
        await message.answer(
            "🤖 Я бот для заказа еды!\n\n"
            "Используйте команду /start или кнопки."
        )

# ========== ЗАПУСК БОТА ==========
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
