# bot.py - Простой рабочий бот
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Импортируем конфиг и меню
try:
    from config import BOT_TOKEN, CUISINES
    from menus import MENUS, burger_menu, italy_menu, sushi_menu
    print("✅ Конфиг и меню загружены")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Проверьте наличие файлов:")
    print("1. config.py с BOT_TOKEN и CUISINES")
    print("2. menus/__init__.py")
    print("3. menus/burger_menu.py, italy_menu.py, sushi_menu.py")
    exit(1)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Временная корзина в памяти
user_carts = {}

# ========== СТАРТОВОЕ МЕНЮ ==========
@dp.message(CommandStart())
async def start(message: types.Message):
    user = message.from_user
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=burger_menu.name, callback_data="show_menu:burger")],
        [InlineKeyboardButton(text=italy_menu.name, callback_data="show_menu:italy")],
        [InlineKeyboardButton(text=sushi_menu.name, callback_data="show_menu:sushi")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart")]
    ])
    
    await message.answer(
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"Добро пожаловать в ресторанный бот!\n"
        f"Выберите кухню:",
        parse_mode="HTML",
        reply_markup=keyboard
    )

# ========== ПОКАЗ МЕНЮ ==========
@dp.callback_query(lambda call: call.data.startswith("show_menu:"))
async def show_menu_handler(call: types.CallbackQuery):
    menu_type = call.data.split(":")[1]
    menu = MENUS.get(menu_type)
    
    if not menu:
        await call.answer("❌ Меню не найдено")
        return
    
    await call.message.edit_text(
        menu.get_menu_text(),
        parse_mode="HTML",
        reply_markup=menu.get_keyboard()
    )
    await call.answer(f"✅ {menu.name}")

# ========== ПОКАЗ БЛЮДА ==========
@dp.callback_query(lambda call: call.data.startswith("menu_item:"))
async def show_item_handler(call: types.CallbackQuery):
    try:
        _, menu_type, item_id = call.data.split(":")
        menu = MENUS.get(menu_type)
        
        if not menu:
            await call.answer("❌ Меню не найдено")
            return
        
        item = menu.get_item_details(item_id)
        if not item:
            await call.answer("❌ Блюдо не найдено")
            return
        
        # Формируем текст
        text = f"""
<b>{item['name']}</b>

{item['description']}

💰 <b>Цена:</b> {item['price']}₽
⚖️ <b>Вес:</b> {item['weight']}г
⏱️ <b>Приготовление:</b> {item['cooking_time']} мин
"""
        if 'calories' in item:
            text += f"🔥 <b>Калории:</b> {item['calories']} ккал\n"
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить в корзину", callback_data=f"add_to_cart:{menu_type}:{item_id}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data=f"show_menu:{menu_type}")]
        ])
        
        await call.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await call.answer()
        
    except Exception as e:
        await call.answer("❌ Ошибка")
        print(f"Error: {e}")

# ========== ДОБАВЛЕНИЕ В КОРЗИНУ ==========
@dp.callback_query(lambda call: call.data.startswith("add_to_cart:"))
async def add_to_cart_handler(call: types.CallbackQuery):
    try:
        _, menu_type, item_id = call.data.split(":")
        menu = MENUS.get(menu_type)
        item = menu.get_item_details(item_id) if menu else None
        
        if not item:
            await call.answer("❌ Блюдо не найдено")
            return
        
        user_id = call.from_user.id
        
        # Инициализируем корзину
        if user_id not in user_carts:
            user_carts[user_id] = []
        
        # Добавляем товар
        user_carts[user_id].append({
            'name': item['name'],
            'price': item['price'],
            'quantity': 1,
            'total': item['price']
        })
        
        await call.answer(f"✅ {item['name']} добавлен в корзину!")
        
        # Возвращаемся к меню
        await show_menu_handler(call)
        
    except Exception as e:
        await call.answer("❌ Ошибка")
        print(f"Error: {e}")

# ========== ПОКАЗ КОРЗИНЫ ==========
@dp.callback_query(lambda call: call.data == "show_cart")
async def show_cart_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    cart_items = user_carts.get(user_id, [])
    
    if not cart_items:
        text = "🛒 <b>Ваша корзина пуста</b>\n\nДобавьте товары из меню!"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍽️ К меню", callback_data="back_to_main")]
        ])
    else:
        # Формируем текст корзины
        text = "🛒 <b>Ваша корзина</b>\n\n"
        total = 0
        
        for idx, item in enumerate(cart_items, 1):
            text += f"{idx}. {item['name']}\n"
            text += f"   {item['quantity']} × {item['price']}₽ = {item['total']}₽\n\n"
            total += item['total']
        
        text += f"💵 <b>Итого: {total}₽</b>"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="◀️ Продолжить покупки", callback_data="back_to_main")]
        ])
    
    await call.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await call.answer()

# ========== ОЧИСТКА КОРЗИНЫ ==========
@dp.callback_query(lambda call: call.data == "clear_cart")
async def clear_cart_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id in user_carts:
        user_carts[user_id] = []
    await show_cart_handler(call)
    await call.answer("🗑️ Корзина очищена")

# ========== ВОЗВРАТ НА ГЛАВНУЮ ==========
@dp.callback_query(lambda call: call.data == "back_to_main")
async def back_to_main_handler(call: types.CallbackQuery):
    user = call.from_user
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=burger_menu.name, callback_data="show_menu:burger")],
        [InlineKeyboardButton(text=italy_menu.name, callback_data="show_menu:italy")],
        [InlineKeyboardButton(text=sushi_menu.name, callback_data="show_menu:sushi")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart")]
    ])
    
    await call.message.edit_text(
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"Выберите кухню:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await call.answer()

# ========== ОФОРМЛЕНИЕ ЗАКАЗА ==========
@dp.callback_query(lambda call: call.data == "checkout")
async def checkout_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    cart_items = user_carts.get(user_id, [])
    
    if not cart_items:
        await call.answer("❌ Корзина пуста")
        return
    
    # Формируем заказ
    order_text = "✅ <b>Заказ оформлен!</b>\n\n"
    total = 0
    
    for item in cart_items:
        order_text += f"• {item['name']} - {item['price']}₽\n"
        total += item['price']
    
    order_text += f"\n💵 <b>Итого: {total}₽</b>\n\n"
    order_text += "Спасибо за заказ! Ожидайте звонка оператора."
    
    # Очищаем корзину
    user_carts[user_id] = []
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍽️ Сделать новый заказ", callback_data="back_to_main")]
    ])
    
    await call.message.edit_text(
        order_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await call.answer("✅ Заказ принят!")

# ========== ОБРАБОТКА ОСТАЛЬНЫХ КОМАНД ==========
@dp.message()
async def handle_other_messages(message: types.Message):
    await message.answer(
        "👋 Используйте кнопки меню или команду /start",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
        ])
    )

# ========== ЗАПУСК БОТА ==========
async def main():
    print("=" * 50)
    print("🚀 Бот запускается...")
    print(f"📱 Токен: {BOT_TOKEN[:10]}...")
    print("🍽️  Доступные кухни:")
    for key, value in CUISINES.items():
        print(f"   • {key}: {value}")
    print("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
