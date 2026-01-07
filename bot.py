# bot.py - Объединенный красивый бот (Исправленная версия)
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импортируем наши меню
from menus import MENUS, burger_menu, italy_menu, sushi_menu

# Инициализация бота (ЗАМЕНИТЕ НА СВОЙ ТОКЕН)
bot = Bot(token="ВАШ_ТОКЕН_ЗДЕСЬ")
dp = Dispatcher()

# Временное хранилище для корзины (в реальном проекте используйте БД)
user_carts = {}

# ========== КРАСИВОЕ ГЛАВНОЕ МЕНЮ ==========
@dp.message(CommandStart())
async def start(message: types.Message):
    user = message.from_user
    
    # Создаем красивую клавиатуру
    builder = InlineKeyboardBuilder()
    
    # Основные кнопки кухонь
    buttons = [
        (f"{burger_menu.icon} {burger_menu.name}", f"show_menu:burger"),
        (f"{italy_menu.icon} {italy_menu.name}", f"show_menu:italy"),
        (f"{sushi_menu.icon} {sushi_menu.name}", f"show_menu:sushi"),
        ("🎯 Рекомендации", "recommendations"),
        ("⭐ Избранное", "favorites"),
        ("📊 Топ продаж", "top_sales")
    ]
    
    for text, callback_data in buttons:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=callback_data
        ))
    
    builder.adjust(2, 2, 1, 1)  # Настройка расположения
    
    # Информационные кнопки
    builder.row(
        InlineKeyboardButton(text="ℹ️ О нас", callback_data="about"),
        InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")
    )

    # Красивое приветственное сообщение
    welcome_text = f"""
🌟 <b>Добро пожаловать, {user.first_name}!</b> 🌟

🍽️ <b>Food Delivery</b> - ваш гастрономический гид!

✨ <b>Что у нас есть:</b>
• {burger_menu.icon} <b>{burger_menu.name}</b> - {burger_menu.description}
• {italy_menu.icon} <b>{italy_menu.name}</b> - {italy_menu.description}
• {sushi_menu.icon} <b>{sushi_menu.name}</b> - {sushi_menu.description}

🎁 <b>Специальные предложения:</b>
🔥 Первый заказ со скидкой <b>20%</b>
🚚 Бесплатная доставка от <b>1500₽</b>
⏰ Доставка за <b>30 минут</b> или бесплатно!

👇 <b>Выберите кухню или воспользуйтесь навигацией:</b>
"""
    
    await message.answer_photo(
        photo="https://via.placeholder.com/1200x400/FF6B6B/FFFFFF?text=Food+Delivery",
        caption=welcome_text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

# ========== КРАСИВОЕ МЕНЮ КУХНИ ==========
@dp.callback_query(lambda call: call.data.startswith("show_menu:"))
async def show_menu_handler(call: types.CallbackQuery):
    menu_type = call.data.split(":")[1]
    menu = MENUS.get(menu_type)
    
    if not menu:
        await call.answer("❌ Меню не найдено", show_alert=True)
        return
    
    try:
        # Показываем анимацию загрузки
        loading_msg = await call.message.answer("🔄 <b>Загружаем меню...</b>", parse_mode="HTML")
        await asyncio.sleep(0.5)
        await loading_msg.delete()
        
        # Форматируем текст меню
        min_price = min(item['price'] for item in menu.items) if menu.items else 0
        avg_time = sum(item['cooking_time'] for item in menu.items) // len(menu.items) if menu.items else 0
        
        menu_text = f"""
{menu.icon * 3} <b>{menu.name.upper()}</b> {menu.icon * 3}

📋 <b>КАТАЛОГ БЛЮД</b>
━━━━━━━━━━━━━━━━━━━━
{menu.get_menu_text()}

🎯 <b>ПОПУЛЯРНОЕ СЕЙЧАС:</b>
🔥 Самые заказываемые блюда
⭐ Выбор наших шеф-поваров
🚀 Быстрее всего готовятся

💰 <b>ЦЕНЫ ОТ:</b> {min_price}₽
⏱️ <b>СРЕДНЕЕ ВРЕМЯ:</b> {avg_time} мин
⭐ <b>РЕЙТИНГ:</b> {'★' * 4}☆ (4.8/5)
"""
        
        # Создаем интерактивную клавиатуру
        builder = InlineKeyboardBuilder()
        
        # Кнопки блюд
        for item in menu.items:
            # Определяем эмодзи для блюда
            emoji_map = {
                'burger': '🍔', 'pizza': '🍕', 'pasta': '🍝',
                'sushi': '🍣', 'roll': '🍙', 'set': '🎌',
                'dessert': '🍰', 'salad': '🥗', 'classic': '👑',
                'spicy': '🌶️', 'cheese': '🧀', 'chicken': '🍗',
                'vegan': '🌱', 'philadelphia': '🇺🇸', 'california': '☀️',
                'salmon': '🐟', 'shrimp': '🍤', 'margherita': '🇮🇹',
                'pepperoni': '🌭', 'carbonara': '🥓', 'lasagna': '🍝',
                'tiramisu': '🍫'
            }
            
            item_emoji = '🍽️'
            for key, value in emoji_map.items():
                if key in item['id']:
                    item_emoji = value
                    break
            
            builder.add(InlineKeyboardButton(
                text=f"{item_emoji} {item['name']} | {item['price']}₽",
                callback_data=f"menu_item:{menu_type}:{item['id']}"
            ))
        
        builder.adjust(1)  # По одному в ряд
        
        # Навигационные кнопки
        builder.row(
            InlineKeyboardButton(text="🔍 Поиск", callback_data=f"search:{menu_type}"),
            InlineKeyboardButton(text="⭐ Избранное", callback_data=f"favorites:{menu_type}")
        )
        
        builder.row(
            InlineKeyboardButton(text="📊 Фильтры", callback_data=f"filters:{menu_type}"),
            InlineKeyboardButton(text="🎯 Рекомендации", callback_data=f"recommend:{menu_type}")
        )
        
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"),
            InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart")
        )
        
        # Редактируем сообщение
        await call.message.edit_text(
            menu_text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        
        await call.answer(f"✅ Открыто меню: {menu.name}")
        
    except Exception as e:
        await call.answer("❌ Ошибка при загрузке меню", show_alert=True)
        print(f"Error: {e}")

# ========== КРАСИВОЕ ОФОРМЛЕНИЕ БЛЮДА ==========
@dp.callback_query(lambda call: call.data.startswith("menu_item:"))
async def show_item_handler(call: types.CallbackQuery):
    try:
        _, menu_type, item_id = call.data.split(":")
        menu = MENUS.get(menu_type)
        
        if not menu:
            await call.answer("❌ Меню не найдено", show_alert=True)
            return
        
        item = menu.get_item_details(item_id)
        if not item:
            await call.answer("❌ Блюдо не найдено", show_alert=True)
            return
        
        # Создаем красивый текст
        text = f"""
{menu.icon} <b>{item['name'].upper()}</b> {menu.icon}

━━━━━━━━━━━━━━━━━━━━
📝 <b>ОПИСАНИЕ:</b>
{item['description']}

━━━━━━━━━━━━━━━━━━━━
💰 <b>ЦЕНА:</b> <code>{item['price']}₽</code>
"""
        
        # Добавляем детали
        details = []
        
        if 'weight' in item:
            details.append(f"⚖️ <b>Вес:</b> {item['weight']}г")
        if 'pieces' in item:
            details.append(f"🍽️ <b>Количество:</b> {item['pieces']} шт")
        if 'size' in item:
            details.append(f"📏 <b>Размер:</b> {item['size']}")
        if 'calories' in item:
            details.append(f"🔥 <b>Калории:</b> {item['calories']} ккал")
        
        details.append(f"⏱️ <b>Приготовление:</b> {item['cooking_time']} мин")
        
        if details:
            text += "\n".join(details) + "\n"
        
        # Пищевая ценность
        if 'calories' in item:
            proteins = (item['calories'] * 0.3) / 4
            fats = (item['calories'] * 0.4) / 9
            carbs = (item['calories'] * 0.3) / 4
            
            text += f"""
━━━━━━━━━━━━━━━━━━━━
🍎 <b>ПИЩЕВАЯ ЦЕННОСТЬ:</b>
• Белки: {proteins:.1f}г
• Жиры: {fats:.1f}г  
• Углеводы: {carbs:.1f}г
"""
        
        # Клавиатура для блюда
        builder = InlineKeyboardBuilder()
        
        # Основная кнопка добавления
        builder.row(
            InlineKeyboardButton(
                text="🛒 Добавить в корзину",
                callback_data=f"add_to_cart:{menu_type}:{item['id']}:1"
            ),
            width=1
        )
        
        # Управление количеством
        builder.row(
            InlineKeyboardButton(text="➖", callback_data=f"decrease:{menu_type}:{item['id']}"),
            InlineKeyboardButton(text="1 шт", callback_data=f"quantity:{menu_type}:{item['id']}:1"),
            InlineKeyboardButton(text="➕", callback_data=f"increase:{menu_type}:{item['id']}")
        )
        
        # Дополнительные функции
        builder.row(
            InlineKeyboardButton(text="⭐ В избранное", callback_data=f"add_favorite:{menu_type}:{item['id']}"),
            InlineKeyboardButton(text="💬 Отзывы", callback_data=f"reviews:{menu_type}:{item['id']}")
        )
        
        builder.row(
            InlineKeyboardButton(text="📋 Состав", callback_data=f"ingredients:{menu_type}:{item['id']}"),
            InlineKeyboardButton(text="📸 Фото", callback_data=f"photos:{menu_type}:{item['id']}")
        )
        
        # Навигация
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"show_menu:{menu_type}"),
            InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main")
        )
        
        # Пытаемся отправить с фото
        try:
            await call.message.delete()
            await call.message.answer_photo(
                photo=f"https://via.placeholder.com/800x600/4ECDC4/FFFFFF?text={item['name'].replace(' ', '+')}",
                caption=text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            await call.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        
        await call.answer(f"🍽️ Выбрано: {item['name']}")
        
    except Exception as e:
        await call.answer("❌ Ошибка при загрузке блюда", show_alert=True)
        print(f"Error in show_item_handler: {e}")

# ========== КРАСИВОЕ ДОБАВЛЕНИЕ В КОРЗИНУ ==========
@dp.callback_query(lambda call: call.data.startswith("add_to_cart:"))
async def add_to_cart_handler(call: types.CallbackQuery):
    try:
        _, menu_type, item_id, quantity = call.data.split(":")
        menu = MENUS.get(menu_type)
        item = menu.get_item_details(item_id) if menu else None
        
        if not item:
            await call.answer("❌ Блюдо не найдено", show_alert=True)
            return
        
        user_id = call.from_user.id
        
        # Инициализируем корзину пользователя если нет
        if user_id not in user_carts:
            user_carts[user_id] = []
        
        # Проверяем, есть ли уже этот товар в корзине
        cart_item = None
        for cart_item_data in user_carts[user_id]:
            if cart_item_data['item_id'] == item_id and cart_item_data['menu_type'] == menu_type:
                cart_item = cart_item_data
                break
        
        if cart_item:
            # Увеличиваем количество
            cart_item['quantity'] += int(quantity)
            cart_item['total'] = cart_item['quantity'] * cart_item['price']
        else:
            # Добавляем новый товар
            user_carts[user_id].append({
                'item_id': item_id,
                'menu_type': menu_type,
                'name': item['name'],
                'price': item['price'],
                'quantity': int(quantity),
                'total': item['price'] * int(quantity)
            })
        
        # Анимация добавления
        if hasattr(call.message, 'caption') and call.message.caption:
            await call.message.edit_caption(
                caption="🔄 <b>Добавляем в корзину...</b>",
                parse_mode="HTML"
            )
        else:
            await call.message.edit_text(
                "🔄 <b>Добавляем в корзину...</b>",
                parse_mode="HTML"
            )
        
        await asyncio.sleep(0.7)
        
        # Обновляем сообщение с подтверждением
        success_text = f"""
✅ <b>УСПЕШНО ДОБАВЛЕНО!</b>

🎉 <b>{item['name']}</b> теперь в вашей корзине!
💰 Стоимость: <b>{item['price']}₽ × {quantity} = {item['price'] * int(quantity)}₽</b>
📦 Всего товаров в корзине: {sum(item['quantity'] for item in user_carts[user_id])}

<i>Продолжайте выбирать или перейдите в корзину</i>
"""
        
        if hasattr(call.message, 'caption') and call.message.caption:
            original_text = call.message.caption.split("\n━━━━━━━━━━━━━━━━━━━━\n✅")[0]
            await call.message.edit_caption(
                caption=original_text + "\n━━━━━━━━━━━━━━━━━━━━\n" + success_text,
                parse_mode="HTML"
            )
        else:
            original_text = call.message.text.split("\n━━━━━━━━━━━━━━━━━━━━\n✅")[0]
            await call.message.edit_text(
                original_text + "\n━━━━━━━━━━━━━━━━━━━━\n" + success_text,
                parse_mode="HTML"
            )
        
        # Красивое уведомление
        await call.answer(
            f"✅ {item['name']} добавлен!\n💰 {item['price']}₽ × {quantity}",
            show_alert=True
        )
        
    except Exception as e:
        await call.answer("❌ Ошибка при добавлении", show_alert=True)
        print(f"Error in add_to_cart_handler: {e}")

# ========== КРАСИВЫЙ ВОЗВРАТ НА ГЛАВНУЮ ==========
@dp.callback_query(lambda call: call.data == "back_to_main")
async def back_to_main_handler(call: types.CallbackQuery):
    try:
        # Анимация перехода
        await call.message.edit_text("🔄 <b>Возвращаемся на главную...</b>", parse_mode="HTML")
        await asyncio.sleep(0.5)
        
        # Создаем красивую главную
        builder = InlineKeyboardBuilder()
        
        for menu_type, menu in MENUS.items():
            builder.add(InlineKeyboardButton(
                text=f"{menu.icon} {menu.name}",
                callback_data=f"show_menu:{menu_type}"
            ))
        
        builder.adjust(1)
        
        # Дополнительные кнопки
        builder.row(
            InlineKeyboardButton(text="🎯 Рекомендации AI", callback_data="ai_recommendations"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
        )
        
        builder.row(
            InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart"),
            InlineKeyboardButton(text="⭐ Избранное", callback_data="show_favorites")
        )
        
        builder.row(
            InlineKeyboardButton(text="🎁 Акции", callback_data="promotions"),
            InlineKeyboardButton(text="👑 Премиум", callback_data="premium")
        )
        
        # Получаем количество товаров в корзине
        cart_count = sum(item['quantity'] for item in user_carts.get(call.from_user.id, []))
        cart_info = f" ({cart_count})" if cart_count > 0 else ""
        
        await call.message.edit_text(
            f"""
🏠 <b>ГЛАВНОЕ МЕНЮ</b>
━━━━━━━━━━━━━━━━━━━━

✨ <b>Добро пожаловать в мир вкуса!</b>

👇 <b>Выберите кухню:</b>
            
🔥 <b>Сегодня в тренде:</b>
• Филадельфия роллы - 30 заказов
• Пицца Пепперони - 25 заказов  
• Бургер Классический - 20 заказов

🛒 <b>Товаров в корзине:</b> {cart_count}
🎁 <b>Акция дня:</b> Скидка 15% на первый заказ!
""",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        
        await call.answer("🏠 Возврат на главную")
        
    except Exception as e:
        await call.answer("❌ Ошибка", show_alert=True)
        print(f"Error in back_to_main_handler: {e}")

# ========== КРАСИВАЯ КОРЗИНА ==========
@dp.callback_query(lambda call: call.data == "show_cart")
async def show_cart_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    
    # Получаем товары из корзины
    cart_items = user_carts.get(user_id, [])
    
    if not cart_items:
        # Корзина пуста
        cart_text = """
🛒 <b>ВАША КОРЗИНА</b>
━━━━━━━━━━━━━━━━━━━━

😔 <b>Корзина пуста</b>

Добавьте товары из меню, чтобы сделать заказ!
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍔 Посмотреть меню", callback_data="back_to_main")],
            [InlineKeyboardButton(text="🎯 Рекомендации", callback_data="recommendations")]
        ])
        
        await call.message.edit_text(
            cart_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await call.answer("🛒 Корзина пуста")
        return
    
    # Вычисляем общую сумму
    total_sum = sum(item["total"] for item in cart_items)
    
    # Формируем текст корзины
    cart_text = """
🛒 <b>ВАША КОРЗИНА</b>
━━━━━━━━━━━━━━━━━━━━

<b>Товары в корзине:</b>
"""
    
    for idx, item in enumerate(cart_items, 1):
        cart_text += f"""
{idx}. <b>{item['name']}</b>
   ×{item['quantity']} шт. | {item['price']}₽/шт.
   <i>Сумма: {item['total']}₽</i>
"""
    
    # Рассчитываем скидку
    discount = total_sum * 0.15 if total_sum > 0 else 0
    delivery = 0 if total_sum >= 1500 else 200
    
    cart_text += f"""
━━━━━━━━━━━━━━━━━━━━
💰 <b>Товары:</b> {total_sum}₽
🎁 <b>Скидка 15%:</b> -{discount:.0f}₽
🚚 <b>Доставка:</b> {delivery if delivery > 0 else "Бесплатно"}
━━━━━━━━━━━━━━━━━━━━
💵 <b>ИТОГО К ОПЛАТЕ:</b> <u>{total_sum - discount + delivery:.0f}₽</u>

⏱️ <b>Время доставки:</b> 30-45 минут
"""
    
    # Клавиатура корзины
    builder = InlineKeyboardBuilder()
    
    if cart_items:
        builder.row(
            InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout"),
            InlineKeyboardButton(text="🗑️ Очистить корзину", callback_data="clear_cart")
        )
    
    builder.row(
        InlineKeyboardButton(text="➕ Добавить еще", callback_data="back_to_main"),
        InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_cart")
    )
    
    builder.row(
        InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main"),
        InlineKeyboardButton(text="📱 Поддержка", callback_data="support_cart")
    )
    
    await call.message.edit_text(
        cart_text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    
    await call.answer(f"🛒 Корзина: {len(cart_items)} товаров")

# ========== ОЧИСТКА КОРЗИНЫ ==========
@dp.callback_query(lambda call: call.data == "clear_cart")
async def clear_cart_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    
    if user_id in user_carts and user_carts[user_id]:
        cart_count = len(user_carts[user_id])
        user_carts[user_id] = []
        
        await call.message.edit_text(
            f"""
🗑️ <b>КОРЗИНА ОЧИЩЕНА</b>
━━━━━━━━━━━━━━━━━━━━

✅ Удалено {cart_count} товаров

Ваша корзина теперь пуста.
Вы можете добавить новые товары из меню!
""",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍽️ Перейти в меню", callback_data="back_to_main")],
                [InlineKeyboardButton(text="🎁 Посмотреть акции", callback_data="promotions")]
            ])
        )
        await call.answer("🗑️ Корзина очищена")
    else:
        await call.answer("🛒 Корзина уже пуста", show_alert=True)

# ========== ОБРАБОТЧИКИ ДЛЯ УПРАВЛЕНИЯ КОЛИЧЕСТВОМ ==========
@dp.callback_query(lambda call: call.data.startswith("increase:"))
async def increase_quantity(call: types.CallbackQuery):
    _, menu_type, item_id = call.data.split(":")
    await call.answer("➕ Количество увеличено")
    # Здесь можно добавить логику обновления количества в реальном времени

@dp.callback_query(lambda call: call.data.startswith("decrease:"))
async def decrease_quantity(call: types.CallbackQuery):
    _, menu_type, item_id = call.data.split(":")
    await call.answer("➖ Количество уменьшено")
    # Здесь можно добавить логику обновления количества в реальном времени

# ========== КОМАНДА /HELP ==========
@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = """
🤖 <b>ПОМОЩЬ ПО КОМАНДАМ</b>
━━━━━━━━━━━━━━━━━━━━

<b>Основные команды:</b>
/start - Начать работу с ботом
/help - Показать это сообщение
/menu - Показать меню
/cart - Показать корзину

<b>Навигация:</b>
• Используйте кнопки для выбора категорий
• Нажимайте на товары для просмотра деталей
• Добавляйте товары в корзину
• Оформляйте заказ через корзину

<b>Поддержка:</b>
Если у вас возникли проблемы, напишите нам:
📞 support@fooddelivery.com
"""
    
    await message.answer(help_text, parse_mode="HTML")

# ========== КОМАНДА /MENU ==========
@dp.message(Command("menu"))
async def menu_command(message: types.Message):
    # Показываем главное меню
    await start(message)

# ========== КОМАНДА /CART ==========
@dp.message(Command("cart"))
async def cart_command(message: types.Message):
    # Создаем фейковый call для обработки
    class FakeCall:
        def __init__(self, user_id, message):
            self.from_user = type('obj', (object,), {'id': user_id})()
            self.message = message
            self.data = "show_cart"
    
    fake_call = FakeCall(message.from_user.id, message)
    await show_cart_handler(fake_call)

# ========== ОБРАБОТЧИК ОШИБОК ==========
@dp.callback_query(lambda call: True)
async def default_handler(call: types.CallbackQuery):
    if call.data in ["recommendations", "favorites", "top_sales", "about", "contacts", 
                     "ai_recommendations", "stats", "show_favorites", "promotions", 
                     "premium", "checkout", "edit_cart", "support_cart", "suggest_idea"]:
        
        # Красивое сообщение о разработке
        function_name = call.data.replace('_', ' ').title()
        
        await call.message.edit_text(
            f"""
🔧 <b>ФУНКЦИЯ В РАЗРАБОТКЕ</b>
━━━━━━━━━━━━━━━━━━━━

🎉 <b>{function_name}</b> скоро будет доступна!

Наши разработчики усердно трудятся над этой функцией.
Ожидайте обновления в ближайшее время!

📅 <b>Статус:</b> В разработке
⏰ <b>Примерное время:</b> 2-3 недели
""",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")],
                [InlineKeyboardButton(text="💡 Предложить идею", callback_data="suggest_idea")]
            ])
        )
        await call.answer("⚙️ Функция в разработке")
    else:
        await call.answer("❌ Неизвестная команда")

# ========== ОБРАБОТКА ВСЕХ СООБЩЕНИЙ ==========
@dp.message()
async def handle_messages(message: types.Message):
    # Если пользователь отправил текст, а не команду
    if message.text and not message.text.startswith('/'):
        await message.answer(
            """
🤖 <b>Я вас не понял</b>

Используйте кнопки меню или команды:
/start - Начать заказ
/menu - Посмотреть меню
/cart - Открыть корзину
/help - Помощь
""",
            parse_mode="HTML"
        )

# ========== ЗАПУСК БОТА ==========
async def main():
    print("🚀 Бот запускается...")
    print("=" * 50)
    print("🍽️  Food Delivery Bot")
    print("📱 Версия: 3.0 (Исправленная)")
    print("🎨 Дизайн: Premium Edition")
    print("=" * 50)
    print("Доступные команды:")
    print("/start - Начать работу")
    print("/help - Помощь")
    print("/menu - Меню")
    print("/cart - Корзина")
    print("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
