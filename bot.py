# bot.py - Основной файл бота
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Импорты из наших модулей
from config import BOT_TOKEN
from menus import ALL_MENUS, burger_menu, pizza_menu, sushi_menu
from database import db

# Создаем бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ========== ГЛАВНОЕ МЕНЮ ==========
@dp.message(CommandStart())
async def start_command(message: types.Message):
    """Команда /start - главное меню"""
    user = message.from_user
    
    # Получаем количество товаров в корзине
    cart_count = len(db.get_cart(user.id))
    cart_text = f" ({cart_count})" if cart_count > 0 else ""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=burger_menu.name, callback_data="menu:burger")],
        [InlineKeyboardButton(text=pizza_menu.name, callback_data="menu:pizza")],
        [InlineKeyboardButton(text=sushi_menu.name, callback_data="menu:sushi")],
        [
            InlineKeyboardButton(text=f"🛒 Корзина{cart_text}", callback_data="cart"),
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
        ]
    ])
    
    await message.answer(
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"Добро пожаловать в наш ресторан!\n"
        f"Выберите категорию меню:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ========== ПОКАЗ МЕНЮ ==========
@dp.callback_query(lambda c: c.data.startswith("menu:"))
async def show_menu(callback: types.CallbackQuery):
    """Показать конкретное меню"""
    menu_type = callback.data.split(":")[1]
    menu = ALL_MENUS.get(menu_type)
    
    if not menu:
        await callback.answer("Меню не найдено")
        return
    
    await callback.message.edit_text(
        menu.get_menu_text(),
        parse_mode="HTML",
        reply_markup=menu.get_keyboard()
    )
    await callback.answer()


# ========== ПОКАЗ ТОВАРА ==========
@dp.callback_query(lambda c: c.data.startswith("item:"))
async def show_item(callback: types.CallbackQuery):
    """Показать детали товара"""
    _, menu_type, item_id = callback.data.split(":")
    menu = ALL_MENUS.get(menu_type)
    
    if not menu:
        await callback.answer("Ошибка")
        return
    
    item = menu.get_item(item_id)
    if not item:
        await callback.answer("Товар не найден")
        return
    
    # Формируем описание
    text = f"<b>{item['name']}</b>\n\n"
    text += f"{item['description']}\n\n"
    text += f"💰 <b>Цена: {item['price']}₽</b>\n"
    
    if 'weight' in item:
        text += f"⚖️ Вес: {item['weight']}г\n"
    if 'size' in item:
        text += f"📏 Размер: {item['size']}\n"
    if 'pieces' in item:
        text += f"🍽️ Количество: {item['pieces']} шт\n"
    
    text += "\nДобавить в корзину?"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить в корзину", callback_data=f"add:{menu_type}:{item_id}")],
        [InlineKeyboardButton(text="◀️ Назад к меню", callback_data=f"menu:{menu_type}")]
    ])
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


# ========== ДОБАВЛЕНИЕ В КОРЗИНУ ==========
@dp.callback_query(lambda c: c.data.startswith("add:"))
async def add_to_cart(callback: types.CallbackQuery):
    """Добавить товар в корзину"""
    _, menu_type, item_id = callback.data.split(":")
    menu = ALL_MENUS.get(menu_type)
    
    if not menu:
        await callback.answer("Ошибка")
        return
    
    item = menu.get_item(item_id)
    if not item:
        await callback.answer("Товар не найден")
        return
    
    # Добавляем в корзину
    cart_item = {
        "menu": menu_type,
        "id": item_id,
        "name": item["name"],
        "price": item["price"],
        "quantity": 1
    }
    
    cart_count = db.add_to_cart(callback.from_user.id, cart_item)
    
    await callback.answer(f"✅ {item['name']} добавлен! ({cart_count} в корзине)")
    
    # Возвращаем в меню
    await show_menu(callback)


# ========== КОРЗИНА ==========
@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(callback: types.CallbackQuery):
    """Показать корзину"""
    user_id = callback.from_user.id
    cart = db.get_cart(user_id)
    
    if not cart:
        text = "🛒 <b>Ваша корзина пуста</b>\n\nДобавьте товары из меню!"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="main_menu")]
        ])
    else:
        text = "🛒 <b>Ваша корзина</b>\n\n"
        total = 0
        
        for idx, item in enumerate(cart, 1):
            item_total = item["price"] * item["quantity"]
            text += f"{idx}. {item['name']}\n"
            text += f"   {item['price']}₽ × {item['quantity']} = {item_total}₽\n\n"
            total += item_total
        
        text += f"💰 <b>Итого: {total}₽</b>"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="main_menu")]
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
    """Оформить заказ"""
    user_id = callback.from_user.id
    cart = db.get_cart(user_id)
    
    if not cart:
        await callback.answer("Корзина пуста")
        return
    
    # Считаем сумму
    total = sum(item["price"] * item["quantity"] for item in cart)
    
    # Создаем заказ
    order = db.create_order(user_id, cart, total)
    
    # Очищаем корзину
    db.clear_cart(user_id)
    
    # Формируем текст заказа
    text = "✅ <b>Заказ принят!</b>\n\n"
    text += f"<b>Номер заказа:</b> {order['id']}\n"
    text += f"<b>Дата:</b> {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
    
    for item in cart:
        text += f"• {item['name']} - {item['price']}₽\n"
    
    text += f"\n💰 <b>Итого: {total}₽</b>\n\n"
    text += "Спасибо за заказ! Ожидайте звонка оператора."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Новый заказ", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer("✅ Заказ оформлен!")


# ========== ОЧИСТКА КОРЗИНЫ ==========
@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    """Очистить корзину"""
    user_id = callback.from_user.id
    count = db.clear_cart(user_id)
    
    await callback.answer(f"🗑️ Удалено {count} товаров")
    await show_cart(callback)


# ========== НАЗАД В ГЛАВНОЕ МЕНЮ ==========
@dp.callback_query(lambda c: c.data == "main_menu")
async def main_menu(callback: types.CallbackQuery):
    """Вернуться в главное меню"""
    user = callback.from_user
    
    cart_count = len(db.get_cart(user.id))
    cart_text = f" ({cart_count})" if cart_count > 0 else ""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=burger_menu.name, callback_data="menu:burger")],
        [InlineKeyboardButton(text=pizza_menu.name, callback_data="menu:pizza")],
        [InlineKeyboardButton(text=sushi_menu.name, callback_data="menu:sushi")],
        [
            InlineKeyboardButton(text=f"🛒 Корзина{cart_text}", callback_data="cart"),
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
        ]
    ])
    
    await callback.message.edit_text(
        f"👋 <b>{user.first_name}</b>, выберите категорию:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


# ========== ПОМОЩЬ ==========
@dp.callback_query(lambda c: c.data == "help")
async def help_command(callback: types.CallbackQuery):
    """Показать помощь"""
    text = """
🤖 <b>Помощь по боту</b>

<b>Как сделать заказ:</b>
1. Выберите категорию меню
2. Выберите блюдо
3. Добавьте в корзину
4. Перейдите в корзину
5. Оформите заказ

<b>Команды:</b>
/start - Главное меню
/help - Эта справка

<b>Если есть вопросы:</b>
Напишите нам: @support
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


# ========== КОМАНДА /HELP ==========
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Команда /help"""
    await help_command(message)


# ========== ОБРАБОТКА ВСЕХ СООБЩЕНИЙ ==========
@dp.message()
async def handle_all_messages(message: types.Message):
    """Обработка всех остальных сообщений"""
    if message.text and not message.text.startswith('/'):
        await message.answer(
            "🤖 Я бот для заказа еды!\n\n"
            "Используйте команды:\n"
            "/start - Начать заказ\n"
            "/help - Помощь"
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
        # Проверяем бота
        me = await bot.get_me()
        print(f"🤖 Бот: @{me.username}")
        print(f"📛 Имя: {me.first_name}")
        print("✅ Бот готов к работе!")
        print("=" * 50)
        
        # Запускаем
        await dp.start_polling(bot)
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        print("=" * 50)
        print("Возможные причины:")
        print("1. Неверный токен в config.py")
        print("2. Нет интернет соединения")
        print("3. Aiogram не установлен")
        print("=" * 50)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
