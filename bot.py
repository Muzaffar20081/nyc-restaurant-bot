# bot.py — ОСНОВНОЙ ФАЙЛ БОТА С AI
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu import CATEGORIES, ALL_ITEMS, MENU_TEXT
from ai_brain import ask_grok  # Импортируем AI

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

user_cart = defaultdict(list)

# Ссылки на фото
PHOTOS = {
    "start": "https://imgur.com/a/KT9Bn51",
    "menu": "https://imgur.com/a/KT9Bn51", 
    "cart": "https://imgur.com/a/KT9Bn51"
}

@dp.message(CommandStart())
async def start(message: types.Message):
    try:
        await message.answer_photo(
            photo=PHOTOS["start"],
            caption=f"Здарова, {message.from_user.first_name}!\n\n*BURGER KING 2025 ЖИВОЙ НА МАКСИМАЛКАХ*\n\nПиши что хочешь - AI поймет! 🤖",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")],
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
                [InlineKeyboardButton(text="💬 Поговорить с AI", callback_data="chat_mode")]
            ]),
            parse_mode="Markdown"
        )
    except:
        await message.answer(
            f"Здарова, {message.from_user.first_name}!\n\n*BURGER KING 2025 ЖИВОЙ НА МАКСИМАЛКАХ*\n\nПиши что хочешь - AI поймет! 🤖",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")],
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
                [InlineKeyboardButton(text="💬 Поговорить с AI", callback_data="chat_mode")]
            ]),
            parse_mode="Markdown"
        )

@dp.callback_query(lambda c: c.data == "menu")
async def show_categories(call: types.CallbackQuery):
    keyboard = []
    for category_name in CATEGORIES.keys():
        keyboard.append([InlineKeyboardButton(text=category_name, callback_data=f"category_{category_name[2:]}")])
    
    keyboard.append([InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")])
    keyboard.append([InlineKeyboardButton(text="💬 AI Режим", callback_data="chat_mode")])
    
    try:
        await call.message.edit_media(
            media=types.InputMediaPhoto(
                media=PHOTOS["menu"],
                caption=MENU_TEXT
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except:
        await call.message.edit_text(
            text=MENU_TEXT,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("category_"))
async def show_category_items(call: types.CallbackQuery):
    category_key = call.data[9:]
    
    full_category_name = None
    for cat_name in CATEGORIES.keys():
        if cat_name[2:] == category_key:
            full_category_name = cat_name
            break
    
    if not full_category_name:
        await call.answer("❌ Категория не найдена")
        return
    
    items = CATEGORIES[full_category_name]
    
    keyboard = []
    items_list = list(items.items())
    
    for i in range(0, len(items_list), 2):
        row = []
        for j in range(2):
            if i + j < len(items_list):
                item_name, price = items_list[i + j]
                row.append(InlineKeyboardButton(
                    text=f"{item_name} - {price}₽", 
                    callback_data=f"add_{item_name}"
                ))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="menu")])
    keyboard.append([InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")])
    keyboard.append([InlineKeyboardButton(text="💬 AI Режим", callback_data="chat_mode")])
    
    caption = f"*{full_category_name}*\n\nВыбери что хочешь заказать:"
    
    try:
        await call.message.edit_media(
            media=types.InputMediaPhoto(
                media=PHOTOS["menu"],
                caption=caption
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except:
        await call.message.edit_text(
            text=caption,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(call: types.CallbackQuery):
    item_name = call.data[4:]
    user_id = call.from_user.id
    
    if item_name in ALL_ITEMS:
        user_cart[user_id].append({
            "name": item_name,
            "price": ALL_ITEMS[item_name]
        })
        await call.answer(f"✅ {item_name} добавлен в корзину!")
    else:
        await call.answer("❌ Товар не найден")

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    cart_items = user_cart[user_id]
    
    if not cart_items:
        caption = "*🛒 Корзина пуста!*\n\nВыбери что-нибудь из меню 🍔"
        keyboard = [
            [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")],
            [InlineKeyboardButton(text="💬 AI Режим", callback_data="chat_mode")]
        ]
    else:
        total = sum(item["price"] for item in cart_items)
        caption = "*🛒 Твоя корзина:*\n\n"
        
        item_counts = {}
        for item in cart_items:
            name = item["name"]
            item_counts[name] = item_counts.get(name, 0) + 1
        
        for name, count in item_counts.items():
            price = ALL_ITEMS[name]
            caption += f"• {name} ×{count} — {price * count}₽\n"
        
        caption += f"\n💵 *Итого: {total}₽*"
        
        keyboard = [
            [InlineKeyboardButton(text="🧹 Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="🍔 Продолжить покупки", callback_data="menu")],
            [InlineKeyboardButton(text="💬 AI Режим", callback_data="chat_mode")]
        ]
    
    try:
        await call.message.edit_media(
            media=types.InputMediaPhoto(
                media=PHOTOS["cart"],
                caption=caption
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except:
        await call.message.edit_text(
            text=caption,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
    await call.answer()

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_cart[user_id] = []
    await call.answer("🧹 Корзина очищена!")
    await show_cart(call)

@dp.callback_query(lambda c: c.data == "checkout")
async def checkout(call: types.CallbackQuery):
    user_id = call.from_user.id
    cart_items = user_cart[user_id]
    
    if not cart_items:
        await call.answer("❌ Корзина пуста!")
        return
    
    total = sum(item["price"] for item in cart_items)
    user_cart[user_id] = []
    
    order_text = f"✅ *Заказ принят!*\n\n"
    for item in cart_items:
        order_text += f"• {item['name']} — {item['price']}₽\n"
    order_text += f"\n💵 Сумма: {total}₽\n📱 Статус: принят\n\nОжидай уведомление о готовности!"
    
    try:
        await call.message.edit_media(
            media=types.InputMediaPhoto(
                media=PHOTOS["start"],
                caption=order_text
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Новый заказ", callback_data="menu")],
                [InlineKeyboardButton(text="💬 AI Режим", callback_data="chat_mode")]
            ])
        )
    except:
        await call.message.edit_text(
            text=order_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Новый заказ", callback_data="menu")],
                [InlineKeyboardButton(text="💬 AI Режим", callback_data="chat_mode")]
            ]),
            parse_mode="Markdown"
        )
    await call.answer()

@dp.callback_query(lambda c: c.data == "chat_mode")
async def enable_chat_mode(call: types.CallbackQuery):
    await call.message.edit_text(
        text="*💬 AI Режим включен!*\n\nТеперь пиши что хочешь - бот поймет любую фразу!\n\nПримеры:\n• \"Дай два воппера и колу\"\n• \"Сколько стоит в корзине?\"\n• \"Очисти корзину\"\n• \"Что есть поакционнее?\"",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")],
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
        ]),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text.strip()
    
    # Если точное название товара - добавляем сразу
    if user_text in ALL_ITEMS:
        user_cart[user_id].append({
            "name": user_text,
            "price": ALL_ITEMS[user_text]
        })
        await message.answer(f"✅ {user_text} добавлен в корзину!")
        
        cart_items = user_cart[user_id]
        total = sum(item["price"] for item in cart_items)
        
        await message.answer(
            f"*🛒 В корзине товаров на {total}₽*",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
                [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")],
                [InlineKeyboardButton(text="💬 AI Режим", callback_data="chat_mode")]
            ]),
            parse_mode="Markdown"
        )
        return
    
    # Обрабатываем через AI
    cart_items = user_cart[user_id]
    cart_info = "пусто"
    if cart_items:
        total = sum(item["price"] for item in cart_items)
        item_counts = {}
        for item in cart_items:
            name = item["name"]
            item_counts[name] = item_counts.get(name, 0) + 1
        cart_info = ", ".join([f"{name}×{count}" for name, count in item_counts.items()]) + f" - {total}₽"
    
    # Показываем что бот думает
    thinking_msg = await message.answer("🤔 Думаю...")
    
    # Получаем ответ от AI
    ai_response = await ask_grok(user_text, cart_info)
    
    # Удаляем сообщение "Думаю"
    await thinking_msg.delete()
    
    # Отправляем ответ
    await message.answer(
        f"*🤖 Бот:* {ai_response}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")],
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
            [InlineKeyboardButton(text="💬 Еще поговорить", callback_data="chat_mode")]
        ])
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

