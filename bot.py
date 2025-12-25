# bot.py — ФИНАЛЬНЫЙ, ВСЁ СОЕДИНЕНО
import os
import asyncio
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ai_brain import ask_ai  # ← твой AI
from database import load_restaurants, save_order  # ← твоя база

# Загружаем рестораны (из restaurants.json)
restaurants = load_restaurants()
current_restaurant = restaurants[0]  # первый ресторан

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

user_cart = defaultdict(list)

def get_menu_keyboard():
    kb = []
    for item in current_restaurant["menu"]:
        kb.append([InlineKeyboardButton(text=f"{item['name']} — {item['price']}₽", callback_data=f"add_{item['name']}")])
    kb.append([InlineKeyboardButton(text="Корзина", callback_data="cart")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(CommandStart())
async def start(m: types.Message):
    await m.answer_photo(
        "https://i.ibb.co/m9kJ7B/welcome-burger.png",
        caption=f"Здарова, {m.from_user.first_name}!\n\n*BURGER KING 2025 — ТВОЯ КОМАНДА ВКУСА*\n\nВыбери ресторан или пиши заказ!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Открыть меню", callback_data="menu")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )

@dp.callback_query(lambda c: c.data == "menu")
async def show_menu(c: types.CallbackQuery):
    await c.message.edit_caption(
        caption="Выбирай вкусняшку:",
        reply_markup=get_menu_keyboard()
    )
    await c.answer()

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_item(c: types.CallbackQuery):
    item_name = c.data[4:]
    user_id = c.from_user.id
    for item in current_restaurant["menu"]:
        if item["name"] == item_name:
            user_cart[user_id].append(item.copy())
            await c.answer(f"{item_name} добавлен!")
            break
    await c.message.edit_reply_markup(reply_markup=None)

@dp.callback_query(lambda c: c.data == "cart")
async def cart(c: types.CallbackQuery):
    user_id = c.from_user.id
    items = user_cart[user_id]
    if not items:
        text = "Корзина пустая!"
    else:
        total = sum(i["price"] for i in items)
        text = "Твоя корзина:\n\n" + "\n".join([f"{i['name']} — {i['price']}₽" for i in items]) + f"\n\nИтого: {total}₽"
    await c.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Очистить", callback_data="clear")],
        [InlineKeyboardButton(text="Меню", callback_data="menu")]
    ]))
    await c.answer()

@dp.callback_query(lambda c: c.data == "clear")
async def clear(c: types.CallbackQuery):
    user_cart[c.from_user.id].clear()
    await c.answer("Очищено!", show_alert=True)
    await cart(c)

@dp.message()
async def text_handler(m: types.Message):
    answer = await ask_ai(m.text)
    await m.answer(answer)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
