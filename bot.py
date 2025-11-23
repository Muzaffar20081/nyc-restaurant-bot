# bot.py — ОСНОВНОЙ ФАЙЛ БОТА С КАТЕГОРИЯМИ
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu import CATEGORIES, ALL_ITEMS, MENU_TEXT

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

user_cart = defaultdict(list)

# Ссылки на фото
PHOTOS = {
    "start": "https://i.imgur.com/9R0KZbA.jpeg",
    "menu": "https://i.imgur.com/7Q9V9zJ.jpeg", 
    "cart": "https://i.imgur.com/5X8wZ2B.jpeg"
}

@dp.message(CommandStart())
async def start(message: types.Message):
    try:
        await message.answer_photo(
            photo=PHOTOS["start"],
            caption=f"Здарова, {message.from_user.first_name}!\n\n*BURGER KING 2025 ЖИВОЙ НА МАКСИМАЛКАХ*",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")],
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
            ]),
            parse_mode="Markdown"
        )
    except:
        await message.answer(
            f"Здарова, {message.from_user.first_name}!\n\n*BURGER KING 2025 ЖИВОЙ НА МАКСИМАЛКАХ*",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")],
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
            ]),
            parse_mode="Markdown"
        )

@dp.callback_query(lambda c: c.data == "menu")
async def show_categories(call: types.CallbackQuery):
    keyboard = []
    # Создаем кнопки категорий
    for category_name in CATEGORIES.keys():
        keyboard.append([InlineKeyboardButton(text=category_name, callback_data=f"category_{category_name[2:]}")])
    
    keyboard.append([InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")])
    
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
    category_key = call.data[9:]  # Убираем "category_"
    
    # Находим полное название категории с эмодзи
    full_category_name = None
    for cat_name in CATEGORIES.keys():
        if cat_name[2:] == category_key:
            full_category_name = cat_name
            break
    
    if not full_category_name:
        await call.answer("❌ Категория не найдена")
        return
    
    items = CATEGORIES[full_category_name]
    
    # Создаем кнопки товаров
    keyboard = []
    items_list = list(items.items())
    
    # Разбиваем на ряды по 2 кнопки
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
    
    # Кнопки навигации
    keyboard.append([InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="menu")])
    keyboard.append([InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")])
    
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
    item_name = call.data[4:]  # Убираем "add_"
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
        keyboard = [[InlineKeyboardButton(text="🍔 Меню", callback_data="menu")]]
    else:
        total = sum(item["price"] for item in cart_items)
        caption = "*🛒 Твоя корзина:*\n\n"
        
        # Группируем одинаковые товары
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
            [InlineKeyboardButton(text="🍔 Продолжить покупки", callback_data="menu")]
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
                [InlineKeyboardButton(text="🍔 Новый заказ", callback_data="menu")]
            ])
        )
    except:
        await call.message.edit_text(
            text=order_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Новый заказ", callback_data="menu")]
            ]),
            parse_mode="Markdown"
        )
    await call.answer()

@dp.message()
async def handle_text(message: types.Message):
    text = message.text.strip()
    
    if text in ALL_ITEMS:
        user_id = message.from_user.id
        user_cart[user_id].append({
            "name": text,
            "price": ALL_ITEMS[text]
        })
        await message.answer(f"✅ {text} добавлен в корзину!")
        
        cart_items = user_cart[user_id]
        total = sum(item["price"] for item in cart_items)
        
        await message.answer(
            f"*🛒 В корзине товаров на {total}₽*",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
                [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")]
            ]),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "Не понял тебя, брат! Используй кнопки 👇",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Открыть меню", callback_data="menu")]
            ])
        )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
