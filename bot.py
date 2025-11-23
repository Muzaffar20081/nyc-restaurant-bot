# bot.py — 100% РАБОТАЕТ С ТВОИМИ ФАЙЛАМИ (21 ноября 2025)
import asyncio
import os
import json
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu import BEAUTIFUL_MENU

# Загружаем цены из restaurants.json
with open("restaurants.json", "r", encoding="utf-8") as f:
    restaurants_data = json.load(f)
    PRICES = restaurants_data[0]["menu"]  # берём первый ресторан

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

user_cart = defaultdict(list)

def get_cart(user_id):
    if not user_cart[user_id]:
        return "*Корзина пустая, брат!*"
    total = sum(item["price"] * item["qty"] for item in user_cart[user_id])
    text = "*Твоя корзина:*\n\n"
    for item in user_cart[user_id]:
        text += f"• {item['name']} × {item['qty']} = {item['price'] * item['qty']}₽\n"
    text += f"\n*Итого: {total}₽*"
    return text

def add_to_cart(user_id, text):
    text = text.lower()
    added = []
    for name, price in PRICES.items():
        if name.lower() in text:
            found = False
            for item in user_cart[user_id]:
                if item["name"].lower() == name.lower():
                    item["qty"] += 1
                    found = True
                    break
            if not found:
                user_cart[user_id].append({"name": name, "price": price, "qty": 1})
            added.append(name.title())
    return added

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer_photo(
        photo="https://i.ibb.co/m9kJ7B/welcome-burger.png",
        caption=f"Здарова, {message.from_user.first_name}!\n\n*BURGER KING 2025 — ЖИВОЙ НА 1000%*\n\nПиши что хочешь — я добавлю в корзину!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )

@dp.callback_query(lambda c: c.data == "menu")
async def show_menu(call: types.CallbackQuery):
    await call.message.edit_caption(
        caption=BEAUTIFUL_MENU,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    await call.message.edit_caption(
        caption=get_cart(call.from_user.id),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Очистить корзину", callback_data="clear")],
            [InlineKeyboardButton(text="Меню", callback_data="menu")]
        ])
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "clear")
async def clear_cart(call: types.CallbackQuery):
    user_cart[call.from_user.id].clear()
    await call.answer("Корзина очищена!", show_alert=True)
    await show_cart(call)

@dp.message()
async def handle_message(message: types.Message):
    if not message.text:
        return
    added = add_to_cart(message.from_user.id, message.text)
    if added:
        await message.answer(f"Закинул: {', '.join(added)}!\n\n{get_cart(message.from_user.id)}")
    else:
        await message.answer("Пиши что хочешь заказать — воппер, колу, наггетсы... я пойму!")

async def main():
    print("БОТ ЗАПУЩЕН — САМЫЙ КРУТОЙ В РОССИИ 2025")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
