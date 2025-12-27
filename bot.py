# bot.py — ФИНАЛЬНАЯ ВЕРСИЯ С ПОДДЕРЖКОЙ МНОГИХ МЕНЮ (2025)
import asyncio
import os
import logging
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.enums import ParseMode

# Импортируем всё из menus/
from menus import ALL_MENUS, MENU_CATEGORIES, get_menu_by_category, get_all_categories, find_item_by_id
from ai_brain import ask_ai  # твой AI

# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

user_cart = defaultdict(list)  # {user_id: [items]}
user_states = {}  # {user_id: {"category": "burgers", "item": None}}

@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = {"category": None}

    keyboard = create_main_menu_keyboard()
    await message.answer(
        f"Здарова, {message.from_user.first_name}!\n\n"
        "*FOOD EXPRESS 2025 — ВЫБЕРИ ВКУС!*\n\n"
        "Выбери категорию меню:",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

def create_main_menu_keyboard():
    keyboard = []
    categories = get_all_categories()
    for i in range(0, len(categories), 2):
        row = []
        if i < len(categories):
            row.append(InlineKeyboardButton(
                text=categories[i]["name"],
                callback_data=f"category_{categories[i]['id']}"
            ))
        if i + 1 < len(categories):
            row.append(InlineKeyboardButton(
                text=categories[i + 1]["name"],
                callback_data=f"category_{categories[i + 1]['id']}"
            ))
        keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"),
        InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.callback_query(lambda c: c.data.startswith("category_"))
async def show_category_menu(call: types.CallbackQuery):
    category_id = call.data[9:]
    user_id = call.from_user.id
    user_states[user_id]["category"] = category_id

    menu_items = get_menu_by_category(category_id)
    if not menu_items:
        await call.answer("Меню пустое")
        return

    keyboard = []
    for item in menu_items:
        keyboard.append([InlineKeyboardButton(
            text=f"{item.get('image', '')} {item['name']} - {item['price']}₽",
            callback_data=f"item_{item['id']}"
        )])

    keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_categories"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")
    ])

    category_name = next((cat["name"] for cat in get_all_categories() if cat["id"] == category_id), "Меню")

    await call.message.edit_text(
        f"*{category_name}*\n\nВыбери блюдо:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("item_"))
async def show_item_details(call: types.CallbackQuery):
    item_id = call.data[5:]
    item = find_item_by_id(item_id)
    if not item:
        await call.answer("Товар не найден")
        return

    description = f"*{item['name']}*\n\n{item.get('description', '')}\n\n"
    if 'weight' in item:
        description += f"📏 Вес: {item['weight']}\n"
    elif 'size' in item:
        description += f"📏 Размер: {item['size']}\n"
    elif 'pieces' in item:
        description += f"📏 Количество: {item['pieces']}\n"
    description += f"\n💵 Цена: *{item['price']}₽*"

    keyboard = [
        [InlineKeyboardButton(text="➕ Добавить в корзину", callback_data=f"add_{item_id}")],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"back_to_category_{item['category']}"),
            InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")
        ]
    ]

    await call.message.edit_text(
        description,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(call: types.CallbackQuery):
    item_id = call.data[4:]
    item = find_item_by_id(item_id)
    if not item:
        await call.answer("Товар не найден")
        return

    user_id = call.from_user.id
    user_cart[user_id].append(item.copy())
    await call.answer(f"{item['name']} добавлен в корзину!")
    await call.message.edit_reply_markup(reply_markup=None)

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    items = user_cart.get(user_id, [])
    if not items:
        caption = "*🛒 Корзина пуста!*"
        keyboard = [[InlineKeyboardButton(text="Меню", callback_data="back_to_categories")]]
    else:
        total = sum(item["price"] for item in items)
        item_counts = {}
        for item in items:
            name = item["name"]
            item_counts[name] = item_counts.get(name, 0) + 1

        caption = "*🛒 Корзина:*\n\n"
        for name, count in item_counts.items():
            price = next(i["price"] for i in items if i["name"] == name)
            caption += f"• {name} ×{count} = {price * count}₽\n"
        caption += f"\n💰 *Итого: {total}₽*"
        keyboard = [
            [InlineKeyboardButton(text="🧹 Очистить", callback_data="clear_cart")],
            [InlineKeyboardButton(text="✅ Оформить", callback_data="checkout")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data="back_to_categories")]
        ]

    await call.message.edit_text(caption, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode=ParseMode.MARKDOWN)
    await call.answer()

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(call: types.CallbackQuery):
    user_cart[call.from_user.id].clear()
    await call.answer("Корзина очищена!", show_alert=True)
    await show_cart(call)

@dp.callback_query(lambda c: c.data == "checkout")
async def checkout(call: types.CallbackQuery):
    user_id = call.from_user.id
    items = user_cart.get(user_id, [])
    if not items:
        await call.answer("Корзина пуста!")
        return

    total = sum(item["price"] for item in items)
    user_cart[user_id].clear()

    order_text = f"✅ *Заказ принят!*\n\n"
    for item in items:
        order_text += f"• {item['name']} — {item['price']}₽\n"
    order_text += f"\n💵 Сумма: {total}₽\n\nОжидай уведомление!"

    await call.message.edit_text(order_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Новый заказ", callback_data="back_to_categories")]
    ]), parse_mode=ParseMode.MARKDOWN)
    await call.answer()

@dp.message()
async def text_handler(message: types.Message):
    if not message.text:
        return
    answer = await ask_ai(message.text)
    await message.answer(answer)

async def main():
    logging.info("БОТ ЗАПУЩЕН — FOOD EXPRESS 2025")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
