import os
import importlib
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, CAFES, DEFAULT_CAFE
from ai_brain import ask_grok

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_cart = defaultdict(list)
ai_mode = defaultdict(bool)
user_cafe = defaultdict(lambda: DEFAULT_CAFE)

def load_menu(cafe_key):
    """Загружает меню для конкретного кафе"""
    try:
        if cafe_key not in CAFES:
            cafe_key = DEFAULT_CAFE
            
        cafe_config = CAFES[cafe_key]
        module_path = cafe_config["menu_file"]
        
        menu_module = importlib.import_module(module_path)
        return menu_module.CATEGORIES, menu_module.ALL_ITEMS, menu_module.MENU_TEXT
    except Exception as e:
        print(f"❌ Ошибка загрузки меню: {e}")
        return {}, {}, "📋 Меню временно недоступно"

@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    ai_mode[user_id] = False
    
    # Красивая клавиатура выбора кафе
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍝 Итальянское кафе", callback_data="cafe_italy")],
        [InlineKeyboardButton(text="🍣 Суши-бар", callback_data="cafe_sushi")],
        [InlineKeyboardButton(text="🍔 Бургер-хаус", callback_data="cafe_burger")],
    ])
    
    # Красивое приветствие с эмодзи
    welcome_text = """
🎉 *ДОБРО ПОЖАЛОВАТЬ В МИР ВКУСА!* 🎉

✨ *Выбери кухню мечты:* ✨

• 🍝 *Италия* - страсть и паста
• 🍣 *Япония* - гармония и суши  
• 🍔 *Америка* - энергия и бургеры

*Готовы к гастрономическому путешествию?* 🌍
"""
    
    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data.startswith("cafe_"))
async def select_cafe(call: types.CallbackQuery):
    user_id = call.from_user.id
    cafe_key = call.data[5:]  # Получаем "italy", "sushi", "burger"
    
    if cafe_key in CAFES:
        user_cafe[user_id] = cafe_key
        cafe_name = CAFES[cafe_key]["name"]
        cafe_color = CAFES[cafe_key].get("color", "✨")
        cafe_photo = CAFES[cafe_key].get("photo", "")
        
        # Красивая клавиатура для кафе
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Посмотреть меню", callback_data="menu")],
            [InlineKeyboardButton(text="🛒 Моя корзина", callback_data="cart")],
            [InlineKeyboardButton(text="🤖 AI-Помощник", callback_data="chat_mode")],
            [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
        ])
        
        welcome_message = f"""
{cafe_color} {cafe_name}

*Добро пожаловать в мир вкуса!* 🌟

🍽️ *Готовы сделать заказ?*
✨ *Выбирайте удобный способ:*
"""
        
        try:
            if cafe_photo:
                # Отправляем фото с кнопками
                await bot.send_photo(
                    chat_id=call.message.chat.id,
                    photo=cafe_photo,
                    caption=welcome_message,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                # Удаляем старое сообщение
                await call.message.delete()
            else:
                # Если фото нет - редактируем сообщение с кнопками
                await call.message.edit_text(
                    welcome_message,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            # Если ошибка - просто редактируем текст с кнопками
            await call.message.edit_text(
                welcome_message,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        
        await call.answer()
    else:
        await call.answer()

@dp.callback_query(lambda c: c.data.startswith("cafe_"))
async def select_cafe(call: types.CallbackQuery):
    user_id = call.from_user.id
    cafe_key = call.data[5:]
    
    if cafe_key in CAFES:
        user_cafe[user_id] = cafe_key
        cafe_name = CAFES[cafe_key]["name"]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Меню", callback_data="menu")],
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
        ])
        
        await call.message.edit_text(
            f"🏪 {cafe_name}\n\nВыберите действие:",
            reply_markup=keyboard
        )
    
    await call.answer()

@dp.callback_query(lambda c: c.data == "menu")
async def show_categories(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = False
    
    cafe_key = user_cafe[user_id]
    CATEGORIES, ALL_ITEMS, MENU_TEXT = load_menu(cafe_key)
    cafe_name = CAFES[cafe_key]["name"]
    
    # Красивые кнопки категорий
    keyboard = []
    for category_name in CATEGORIES.keys():
        keyboard.append([InlineKeyboardButton(
            text=f"✨ {category_name}", 
            callback_data=f"category_{category_name.replace(' ', '_').replace('🍕', '').replace('🍝', '').replace('🥗', '').replace('🍹', '').replace('🍣', '').replace('🍱', '').replace('🍤', '').replace('🍵', '').replace('🍔', '').replace('🍟', '').replace('🥤', '').replace('🍦', '')}"
        )])
    
    keyboard += [
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
        [InlineKeyboardButton(text="🤖 AI-Помощник", callback_data="chat_mode")],
        [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
    ]
    
    await call.message.edit_text(
        text=f"{MENU_TEXT}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("category_"))
async def show_category_items(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = False
    
    cafe_key = user_cafe[user_id]
    CATEGORIES, ALL_ITEMS, _ = load_menu(cafe_key)
    
    category_key = call.data[9:].replace('_', ' ')
    full_category_name = None
    
    for cat_name in CATEGORIES.keys():
        clean_cat_name = cat_name.replace('🍕', '').replace('🍝', '').replace('🥗', '').replace('🍹', '').replace('🍣', '').replace('🍱', '').replace('🍤', '').replace('🍵', '').replace('🍔', '').replace('🍟', '').replace('🥤', '').replace('🍦', '').strip()
        if clean_cat_name.replace(' ', '_') == category_key:
            full_category_name = cat_name
            break
    
    if not full_category_name:
        await call.answer()
        return
    
    items = CATEGORIES[full_category_name]
    keyboard = []
    items_list = list(items.items())
    
    # Красивые кнопки товаров
    for i in range(0, len(items_list), 2):
        row = []
        for j in range(2):
            if i + j < len(items_list):
                item_name, price = items_list[i + j]
                row.append(InlineKeyboardButton(
                    text=f"{item_name} — {price}₽",
                    callback_data=f"add_{item_name}"
                ))
        keyboard.append(row)
    
    keyboard += [
        [InlineKeyboardButton(text="⬅️ Назад к меню", callback_data="menu")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
    ]
    
    await call.message.edit_text(
        text=f"🎯 *{full_category_name}*\n\n"
             "💫 *Выбирай вкусняшку:* 💫",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    cafe_key = user_cafe[user_id]
    _, ALL_ITEMS, _ = load_menu(cafe_key)
    
    item_name = call.data[4:]
    if item_name in ALL_ITEMS:
        user_cart[user_id].append({
            "name": item_name, 
            "price": ALL_ITEMS[item_name],
            "cafe": cafe_key
        })
        
        # Без всплывающего уведомления
        await call.answer()
    else:
        await call.answer()

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = False
    
    cart_items = user_cart[user_id]
    cafe_key = user_cafe[user_id]
    cafe_name = CAFES[cafe_key]["name"]
    
    if not cart_items:
        text = f"""
{cafe_name}

🛒 *ВАША КОРЗИНА ПУСТА* 🛒

💫 *Давайте наполним её вкусняшками!* 💫
"""
        keyboard = [
            [InlineKeyboardButton(text="📖 Перейти в меню", callback_data="menu")],
            [InlineKeyboardButton(text="🤖 AI-Помощник", callback_data="chat_mode")],
            [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
        ]
    else:
        total = sum(item["price"] for item in cart_items)
        text = f"""
{cafe_name}

🛒 *ВАША КОРЗИНА:* 🛒
"""
        counts = {}
        for item in cart_items:
            name = item["name"]
            counts[name] = counts.get(name, 0) + 1
        
        for name, cnt in counts.items():
            price = counts[name] * next(item["price"] for item in cart_items if item["name"] == name)
            text += f"├ {name}\n"
            text += f"│   ×{cnt} = {price}₽\n"
        
        text += f"\n💰 *ИТОГО: {total}₽* 💰"
        
        keyboard = [
            [InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="📖 Продолжить покупки", callback_data="menu")],
            [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
        ]
    
    await call.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_cart[user_id].clear()
    await call.answer()
    await show_cart(call)

@dp.callback_query(lambda c: c.data == "checkout")
async def checkout(call: types.CallbackQuery):
    user_id = call.from_user.id
    cart_items = user_cart[user_id].copy()
    user_cart[user_id].clear()
    
    if not cart_items:
        await call.answer()
        return
    
    cafe_key = user_cafe[user_id]
    cafe_name = CAFES[cafe_key]["name"]
    total = sum(item["price"] for item in cart_items)
    
    # Красивое оформление заказа
    order_text = f"""
🎉 *ЗАКАЗ ПРИНЯТ!* 🎉

🏪 *Из:* {cafe_name}

📦 *Ваш заказ:*
"""
    counts = {}
    for item in cart_items:
        name = item["name"]
        counts[name] = counts.get(name, 0) + 1
    
    for name, cnt in counts.items():
        price = counts[name] * next(item["price"] for item in cart_items if item["name"] == name)
        order_text += f"├ {name}\n"
        order_text += f"│   ×{cnt} = {price}₽\n"
    
    order_text += f"\n💰 *СУММА ЗАКАЗА: {total}₽* 💰\n\n"
    order_text += "⏰ *Менеджер свяжется с вами в ближайшее время!*\n"
    order_text += "📞 *Ожидайте звонка!*"
    
    await call.message.edit_text(
        text=order_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍽 Сделать новый заказ", callback_data="menu")]
        ]),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "chat_mode")
async def enable_chat_mode(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = True
    cafe_key = user_cafe[user_id]
    cafe_name = CAFES[cafe_key]["name"]
    
    await call.message.edit_text(
        f"""
{cafe_name}

🤖 *AI-ПОМОЩНИК АКТИВИРОВАН!* 🤖

💫 *Теперь просто напиши что хочешь:*

• 🍕 "2 пиццы и колу"
• 🛒 "Покажи корзину" 
• 🗑 "Очисти корзину"
• 💡 "Что посоветуешь?"
• ❓ "Что популярного?"

🎯 *Я всё пойму и помогу!* 🎯
""",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Вернуться в меню", callback_data="menu")],
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
            [InlineKeyboardButton(text="❌ Выключить AI", callback_data="disable_ai")]
        ]),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "disable_ai")
async def disable_ai_mode(call: types.CallbackQuery):
    user_id = call.from_user.id
    ai_mode[user_id] = False
    cafe_key = user_cafe[user_id]
    cafe_name = CAFES[cafe_key]["name"]
    
    await call.message.edit_text(
        f"""
{cafe_name}

🤖 *AI-ПОМОЩНИК ОТКЛЮЧЁН* 🤖

✨ *Используй кнопки для навигации:* ✨
""",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Меню", callback_data="menu")],
            [InlineKeyboardButton(text="🤖 Включить AI", callback_data="chat_mode")],
            [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
        ]),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    cafe_key = user_cafe[user_id]
    _, ALL_ITEMS, _ = load_menu(cafe_key)
    
    # Проверяем AI режим
    if ai_mode.get(user_id, False):
        # Подготавливаем информацию о корзине
        cart_items = user_cart[user_id]
        cart_info = "🛒 пустая"
        if cart_items:
            total = sum(item["price"] for item in cart_items)
            counts = {}
            for item in cart_items:
                counts[item["name"]] = counts.get(item["name"], 0) + 1
            cart_info = "🛒 " + ", ".join(f"{n}×{c}" for n, c in counts.items()) + f" → {total}₽"
        
        # Используем AI
        response = await ask_grok(text, cart_info, cafe_key, ALL_ITEMS)
        
        await message.answer(
            f"🤖 *AI-Помощник:*\n\n{response}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📖 Меню", callback_data="menu")],
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
                [InlineKeyboardButton(text="❌ Выключить AI", callback_data="disable_ai")]
            ])
        )
    else:
        await message.answer(
            """
🤔 *Не понял команду*

✨ *Выбери способ заказа:* ✨
""",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📖 Меню", callback_data="menu")],
                [InlineKeyboardButton(text="🤖 Включить AI", callback_data="chat_mode")],
                [InlineKeyboardButton(text="🔄 Сменить кафе", callback_data="change_cafe")]
            ])
        )

async def main():
    print("🎉 Бот запущен! Готов к работе! 🍽️")
    print("✨ Красивое меню активировано!")
    print("🤖 AI-помощник готов помочь!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

