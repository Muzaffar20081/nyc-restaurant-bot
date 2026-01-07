# bot.py - Полностью рабочий бот
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# Импортируем конфиг
try:
    from config import BOT_TOKEN
    print(f"✅ Токен загружен: {BOT_TOKEN[:10]}...")
except ImportError:
    print("❌ Ошибка: Не найден файл config.py с BOT_TOKEN")
    print("Создайте файл config.py со следующим содержимым:")
    print('BOT_TOKEN = "ваш_токен_от_BotFather"')
    exit(1)

# Импортируем меню
try:
    from menus import MENUS, burger_menu, italy_menu, sushi_menu
    print("✅ Меню загружены успешно")
except ImportError as e:
    print(f"❌ Ошибка загрузки меню: {e}")
    print("Убедитесь, что в папке menus есть все файлы:")
    print("• __init__.py")
    print("• burger_menu.py")
    print("• italy_menu.py")
    print("• sushi_menu.py")
    exit(1)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Временное хранилище корзин пользователей
user_carts = {}

# ========== КОМАНДА /START ==========
@dp.message(CommandStart())
async def start_command(message: types.Message):
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
        f"Выберите кухню или перейдите в корзину:",
        reply_markup=keyboard
    )

# ========== КОМАНДА /HELP ==========
@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = """
<b>🍽️ Помощь по боту:</b>

<b>Основные команды:</b>
/start - Начать работу с ботом
/help - Показать это сообщение
/menu - Показать главное меню
/cart - Показать корзину

<b>Как пользоваться:</b>
1. Нажмите /start
2. Выберите кухню
3. Выберите блюдо
4. Добавьте в корзину
5. Оформите заказ

<b>Поддержка:</b>
По вопросам пишите: @ваш_ник
"""
    
    await message.answer(help_text)

# ========== КОМАНДА /MENU ==========
@dp.message(Command("menu"))
async def menu_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=burger_menu.name, callback_data="show_menu:burger")],
        [InlineKeyboardButton(text=italy_menu.name, callback_data="show_menu:italy")],
        [InlineKeyboardButton(text=sushi_menu.name, callback_data="show_menu:sushi")]
    ])
    
    await message.answer(
        "🍽️ <b>Выберите кухню:</b>",
        reply_markup=keyboard
    )

# ========== КОМАНДА /CART ==========
@dp.message(Command("cart"))
async def cart_command(message: types.Message):
    # Вызываем обработчик корзины
    await show_cart_for_user(message.from_user.id, message)

# ========== ПОКАЗ МЕНЮ ==========
@dp.callback_query(lambda call: call.data.startswith("show_menu:"))
async def show_menu_handler(call: types.CallbackQuery):
    try:
        menu_type = call.data.split(":")[1]
        menu = MENUS.get(menu_type)
        
        if not menu:
            await call.answer("❌ Меню не найдено")
            return
        
        await call.message.edit_text(
            menu.get_menu_text(),
            reply_markup=menu.get_keyboard()
        )
        await call.answer(f"📋 {menu.name}")
        
    except Exception as e:
        await call.answer("❌ Ошибка")
        print(f"Error in show_menu_handler: {e}")

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
        
        # Формируем описание
        text = f"""
<b>{item['name']}</b>

{item['description']}

<b>Цена:</b> {item['price']}₽
<b>Вес:</b> {item['weight']}г
<b>Приготовление:</b> {item['cooking_time']} мин
"""
        
        # Добавляем дополнительную информацию
        if 'calories' in item:
            text += f"<b>Калории:</b> {item['calories']} ккал\n"
        if 'pieces' in item:
            text += f"<b>Количество:</b> {item['pieces']} шт\n"
        if 'size' in item:
            text += f"<b>Размер:</b> {item['size']}\n"
        
        text += f"\nХотите добавить в корзину?"
        
        # Клавиатура для блюда
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить в корзину", callback_data=f"add_cart:{menu_type}:{item_id}")],
            [InlineKeyboardButton(text="◀️ Назад к меню", callback_data=f"show_menu:{menu_type}")]
        ])
        
        await call.message.edit_text(
            text,
            reply_markup=keyboard
        )
        await call.answer()
        
    except Exception as e:
        await call.answer("❌ Ошибка")
        print(f"Error in show_item_handler: {e}")

# ========== ДОБАВЛЕНИЕ В КОРЗИНУ ==========
@dp.callback_query(lambda call: call.data.startswith("add_cart:"))
async def add_to_cart_handler(call: types.CallbackQuery):
    try:
        _, menu_type, item_id = call.data.split(":")
        menu = MENUS.get(menu_type)
        item = menu.get_item_details(item_id) if menu else None
        
        if not item:
            await call.answer("❌ Блюдо не найдено")
            return
        
        user_id = call.from_user.id
        
        # Инициализируем корзину, если её нет
        if user_id not in user_carts:
            user_carts[user_id] = []
        
        # Добавляем товар в корзину
        user_carts[user_id].append({
            'menu_type': menu_type,
            'item_id': item_id,
            'name': item['name'],
            'price': item['price'],
            'quantity': 1
        })
        
        await call.answer(f"✅ {item['name']} добавлен в корзину!")
        
        # Возвращаемся в меню
        await show_menu_handler(call)
        
    except Exception as e:
        await call.answer("❌ Ошибка при добавлении")
        print(f"Error in add_to_cart_handler: {e}")

# ========== ПОКАЗ КОРЗИНЫ ==========
async def show_cart_for_user(user_id, message_or_call):
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
            item_total = item['price'] * item['quantity']
            text += f"{idx}. <b>{item['name']}</b>\n"
            text += f"   {item['price']}₽ × {item['quantity']} = {item_total}₽\n\n"
            total += item_total
        
        text += f"💵 <b>Итого: {total}₽</b>\n\n"
        
        # Проверяем бесплатную доставку
        if total >= 1500:
            text += "🚚 <b>Доставка: Бесплатно</b> (заказ от 1500₽)\n"
        else:
            text += f"🚚 <b>Доставка: 200₽</b> (до бесплатной доставки осталось {1500 - total}₽)\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="◀️ Продолжить покупки", callback_data="back_to_main")]
        ])
    
    # Определяем, как отправлять сообщение
    if isinstance(message_or_call, types.Message):
        await message_or_call.answer(text, reply_markup=keyboard)
    else:
        await message_or_call.message.edit_text(text, reply_markup=keyboard)

@dp.callback_query(lambda call: call.data == "show_cart")
async def show_cart_handler(call: types.CallbackQuery):
    await show_cart_for_user(call.from_user.id, call)
    await call.answer()

# ========== ОЧИСТКА КОРЗИНЫ ==========
@dp.callback_query(lambda call: call.data == "clear_cart")
async def clear_cart_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    
    if user_id in user_carts and user_carts[user_id]:
        user_carts[user_id] = []
        await show_cart_for_user(user_id, call)
        await call.answer("🗑️ Корзина очищена")
    else:
        await call.answer("🛒 Корзина уже пуста")

# ========== ОФОРМЛЕНИЕ ЗАКАЗА ==========
@dp.callback_query(lambda call: call.data == "checkout")
async def checkout_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    cart_items = user_carts.get(user_id, [])
    
    if not cart_items:
        await call.answer("❌ Корзина пуста")
        return
    
    # Рассчитываем итог
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    delivery = 0 if subtotal >= 1500 else 200
    total = subtotal + delivery
    
    # Формируем заказ
    order_text = f"✅ <b>Заказ оформлен!</b>\n\n"
    order_text += f"<b>Детали заказа:</b>\n"
    
    for item in cart_items:
        order_text += f"• {item['name']} - {item['price']}₽ × {item['quantity']}\n"
    
    order_text += f"\n<b>Подытог:</b> {subtotal}₽\n"
    order_text += f"<b>Доставка:</b> {'Бесплатно' if delivery == 0 else f'{delivery}₽'}\n"
    order_text += f"<b>Итого к оплате:</b> {total}₽\n\n"
    order_text += "Спасибо за заказ! Ожидайте звонка оператора для подтверждения."
    
    # Очищаем корзину
    user_carts[user_id] = []
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍽️ Сделать новый заказ", callback_data="back_to_main")]
    ])
    
    await call.message.edit_text(
        order_text,
        reply_markup=keyboard
    )
    await call.answer("✅ Заказ принят!")

# ========== ВОЗВРАТ НА ГЛАВНУЮ ==========
@dp.callback_query(lambda call: call.data == "back_to_main")
async def back_to_main_handler(call: types.CallbackQuery):
    user = call.from_user
    
    # Получаем количество товаров в корзине
    cart_count = len(user_carts.get(call.from_user.id, []))
    cart_text = f" ({cart_count})" if cart_count > 0 else ""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=burger_menu.name, callback_data="show_menu:burger")],
        [InlineKeyboardButton(text=italy_menu.name, callback_data="show_menu:italy")],
        [InlineKeyboardButton(text=sushi_menu.name, callback_data="show_menu:sushi")],
        [InlineKeyboardButton(text=f"🛒 Корзина{cart_text}", callback_data="show_cart")]
    ])
    
    await call.message.edit_text(
        f"👋 <b>{user.first_name}</b>, выберите кухню:",
        reply_markup=keyboard
    )
    await call.answer()

# ========== ОБРАБОТКА ВСЕХ СООБЩЕНИЙ ==========
@dp.message()
async def handle_all_messages(message: types.Message):
    if message.text and message.text.startswith('/'):
        # Если неизвестная команда
        await message.answer(
            "❌ Неизвестная команда\n"
            "Используйте /start чтобы начать"
        )
    else:
        # Если просто текст
        await message.answer(
            "🤖 Я бот для заказа еды!\n\n"
            "Используйте кнопки меню или команды:\n"
            "/start - Начать\n"
            "/menu - Меню\n"
            "/cart - Корзина\n"
            "/help - Помощь"
        )

# ========== ЗАПУСК БОТА ==========
async def main():
    print("=" * 50)
    print("🚀 Ресторанный бот запускается...")
    print(f"🤖 Токен: {BOT_TOKEN[:10]}...")
    print("🍽️  Доступные меню:")
    for key, menu in MENUS.items():
        print(f"   • {key}: {menu.name}")
    print("=" * 50)
    print("📱 Команды бота:")
    print("   /start - Начать работу")
    print("   /menu - Показать меню")
    print("   /cart - Показать корзину")
    print("   /help - Помощь")
    print("=" * 50)
    
    try:
        # Запускаем бота
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        # Закрываем сессию бота
        await bot.session.close()

if __name__ == "__main__":
    # Запускаем бота
    asyncio.run(main())
