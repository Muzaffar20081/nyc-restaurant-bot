# bot.py - Объединенный красивый бот
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импортируем наши меню
from menus import MENUS, burger_menu, italy_menu, sushi_menu

# Инициализация бота
bot = Bot(token="ВАШ_ТОКЕН")
dp = Dispatcher()

# ========== КРАСИВОЕ ГЛАВНОЕ МЕНЮ ==========
@dp.message(CommandStart())
async def start(message: types.Message):
    user = message.from_user
    
    # Создаем красивую клавиатуру
    builder = InlineKeyboardBuilder()
    
    # Основные кнопки кухонь
    buttons = [
        (burger_menu.icon + " " + burger_menu.name, f"show_menu:burger"),
        (italy_menu.icon + " " + italy_menu.name, f"show_menu:italy"),
        (sushi_menu.icon + " " + sushi_menu.name, f"show_menu:sushi"),
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
        photo="https://via.placeholder.com/1200x400?text=Food+Delivery",
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
        menu_text = f"""
{menu.icon * 3} <b>{menu.name.upper()}</b> {menu.icon * 3}

📋 <b>КАТАЛОГ БЛЮД</b>
━━━━━━━━━━━━━━━━━━━━
{menu.get_menu_text()}

🎯 <b>ПОПУЛЯРНОЕ СЕЙЧАС:</b>
🔥 Самые заказываемые блюда
⭐ Выбор наших шеф-поваров
🚀 Быстрее всего готовятся

💰 <b>ЦЕНЫ ОТ:</b> {min(item['price'] for item in menu.items)}₽
⏱️ <b>СРЕДНЕЕ ВРЕМЯ:</b> {sum(item['cooking_time'] for item in menu.items) // len(menu.items)} мин
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
        
        text += "\n".join(details) + "\n"
        
        # Пищевая ценность
        if 'calories' in item:
            text += f"""
━━━━━━━━━━━━━━━━━━━━
🍎 <b>ПИЩЕВАЯ ЦЕННОСТЬ:</b>
• Белки: {(item['calories'] * 0.3) / 4:.1f}г
• Жиры: {(item['calories'] * 0.4) / 9:.1f}г  
• Углеводы: {(item['calories'] * 0.3) / 4:.1f}г
            """
        
        # Клавиатура для блюда
        builder = InlineKeyboardBuilder()
        
        # Основная кнопка добавления
        builder.row(
            InlineKeyboardButton(
                text="🛒 Добавить в корзину",
                callback_data=f"add_to_cart:{menu_type}:{item_id}"
            ),
            width=1
        )
        
        # Управление количеством
        builder.row(
            InlineKeyboardButton(text="➖", callback_data=f"decrease:{menu_type}:{item_id}"),
            InlineKeyboardButton(text="1 шт", callback_data=f"quantity:{menu_type}:{item_id}:1"),
            InlineKeyboardButton(text="➕", callback_data=f"increase:{menu_type}:{item_id}")
        )
        
        # Дополнительные функции
        builder.row(
            InlineKeyboardButton(text="⭐ В избранное", callback_data=f"add_favorite:{menu_type}:{item_id}"),
            InlineKeyboardButton(text="💬 Отзывы", callback_data=f"reviews:{menu_type}:{item_id}")
        )
        
        builder.row(
            InlineKeyboardButton(text="📋 Состав", callback_data=f"ingredients:{menu_type}:{item_id}"),
            InlineKeyboardButton(text="📸 Фото", callback_data=f"photos:{menu_type}:{item_id}")
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
                photo=f"https://via.placeholder.com/800x600?text={item['name'].replace(' ', '+')}",
                caption=text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        except:
            await call.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        
        await call.answer(f"🍽️ Выбрано: {item['name']}")
        
    except Exception as e:
        await call.answer("❌ Ошибка при загрузке блюда", show_alert=True)

# ========== КРАСИВОЕ ДОБАВЛЕНИЕ В КОРЗИНУ ==========
@dp.callback_query(lambda call: call.data.startswith("add_to_cart:"))
async def add_to_cart_handler(call: types.CallbackQuery):
    try:
        _, menu_type, item_id = call.data.split(":")
        menu = MENUS.get(menu_type)
        item = menu.get_item_details(item_id) if menu else None
        
        if not item:
            await call.answer("❌ Блюдо не найдено", show_alert=True)
            return
        
        # Анимация добавления
        original_text = call.message.text or call.message.caption
        await call.message.edit_caption(
            caption="🔄 <b>Добавляем в корзину...</b>",
            parse_mode="HTML"
        ) if call.message.caption else await call.message.edit_text(
            "🔄 <b>Добавляем в корзину...</b>",
            parse_mode="HTML"
        )
        
        await asyncio.sleep(0.7)
        
        # Здесь должна быть логика добавления в БД
        # cart.add_item(call.from_user.id, item_id, menu_type, item['price'])
        
        # Обновляем сообщение с подтверждением
        new_text = original_text + "\n\n" + f"""
━━━━━━━━━━━━━━━━━━━━
✅ <b>УСПЕШНО ДОБАВЛЕНО!</b>

🎉 <b>{item['name']}</b> теперь в вашей корзине!
💰 Стоимость: <b>{item['price']}₽</b>
📦 <i>Продолжайте выбирать или перейдите в корзину</i>
        """
        
        if call.message.caption:
            await call.message.edit_caption(
                caption=new_text,
                parse_mode="HTML"
            )
        else:
            await call.message.edit_text(
                new_text,
                parse_mode="HTML"
            )
        
        # Красивое уведомление
        await call.answer(
            f"✅ {item['name']} добавлен!\n💰 Цена: {item['price']}₽",
            show_alert=True
        )
        
    except Exception as e:
        await call.answer("❌ Ошибка при добавлении", show_alert=True)

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
        
        await call.message.edit_text(
            """
🏠 <b>ГЛАВНОЕ МЕНЮ</b>
━━━━━━━━━━━━━━━━━━━━

✨ <b>Добро пожаловать в мир вкуса!</b>

👇 <b>Выберите кухню:</b>
            
🔥 <b>Сегодня в тренде:</b>
• Филадельфия роллы - 30 заказов
• Пицца Пепперони - 25 заказов  
• Бургер Классический - 20 заказов

🎁 <b>Акция дня:</b> Скидка 15% на первый заказ!
            """,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        
        await call.answer("🏠 Возврат на главную")
        
    except Exception as e:
        await call.answer("❌ Ошибка", show_alert=True)

# ========== КРАСИВАЯ КОРЗИНА ==========
@dp.callback_query(lambda call: call.data == "show_cart")
async def show_cart_handler(call: types.CallbackQuery):
    # Здесь должна быть логика получения корзины из БД
    # cart_items = get_cart_items(call.from_user.id)
    
    # Для примера создаем тестовую корзину
    cart_items = [
        {"name": "Классический бургер", "price": 350, "quantity": 2, "total": 700},
        {"name": "Пицца Маргарита", "price": 550, "quantity": 1, "total": 550},
        {"name": "Роллы Филадельфия", "price": 450, "quantity": 1, "total": 450},
    ]
    
    total_sum = sum(item["total"] for item in cart_items)
    
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
    
    cart_text += f"""
━━━━━━━━━━━━━━━━━━━━
💰 <b>ИТОГО: {total_sum}₽</b>

🚚 <b>Доставка:</b> Бесплатно (от 1500₽)
⏱️ <b>Время доставки:</b> 30-45 минут
🎁 <b>Ваша скидка:</b> 15% на первый заказ
"""
    
    # Клавиатура корзины
    builder = InlineKeyboardBuilder()
    
    if cart_items:
        builder.row(
            InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout"),
            InlineKeyboardButton(text="🔄 Очистить корзину", callback_data="clear_cart")
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
    
    await call.answer("🛒 Открыта корзина")

# ========== ОБРАБОТЧИКИ ДЛЯ УПРАВЛЕНИЯ КОЛИЧЕСТВОМ ==========
@dp.callback_query(lambda call: call.data.startswith("increase:"))
async def increase_quantity(call: types.CallbackQuery):
    _, menu_type, item_id = call.data.split(":")
    # Здесь логика увеличения количества
    await call.answer("➕ Количество увеличено")

@dp.callback_query(lambda call: call.data.startswith("decrease:"))
async def decrease_quantity(call: types.CallbackQuery):
    _, menu_type, item_id = call.data.split(":")
    # Здесь логика уменьшения количества
    await call.answer("➖ Количество уменьшено")

# ========== ОБРАБОТЧИК ОШИБОК ==========
@dp.callback_query(lambda call: True)
async def default_handler(call: types.CallbackQuery):
    if call.data in ["recommendations", "favorites", "top_sales", "about", "contacts", 
                     "ai_recommendations", "stats", "show_favorites", "promotions", 
                     "premium", "checkout", "clear_cart", "edit_cart", "support_cart"]:
        
        # Красивое сообщение о разработке
        await call.message.edit_text(
            f"""
🔧 <b>ФУНКЦИЯ В РАЗРАБОТКЕ</b>
━━━━━━━━━━━━━━━━━━━━

🎉 <b>{call.data.replace('_', ' ').title()}</b> скоро будет доступна!

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

# ========== ЗАПУСК БОТА ==========
async def main():
    print("🚀 Бот запускается...")
    print("=" * 50)
    print("🍽️  Food Delivery Bot")
    print("📱 Версия: 2.0 (Красивая версия)")
    print("🎨 Дизайн: Premium")
    print("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
