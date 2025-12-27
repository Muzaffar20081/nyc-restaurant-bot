# bot.py — ФИНАЛЬНЫЙ РАБОЧИЙ КОД 2025 (использует твои файлы)
import asyncio
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ai_brain import ask_ai  # ← твой AI
from database import load_restaurants  # ← твоя база

# Загружаем рестораны
restaurants = load_restaurants()
current_menu = restaurants[0]["menu"] if restaurants else {}  # берём первый ресторан

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

user_cart = defaultdict(list)

def get_cart_text(uid):
    if not user_cart[uid]:
        return "*Корзина пустая*"
    total = sum(item["price"] * item["qty"] for item in user_cart[uid])
    text = "*Твоя корзина:*\n\n"
    for item in user_cart[uid]:
        text += f"• {item['name']} × {item['qty']} = {item['price']*item['qty']}₽\n"
    text += f"\n*Итого: {total}₽*"
    return text

def add_to_cart(uid, text):
    text = text.lower()
    added = []
    for name, price in current_menu.items():
        if name.lower() in text:
            found = False
            for item in user_cart[uid]:
                if item["name"] == name:
                    item["qty"] += 1
                    found = True
                    break
            if not found:
                user_cart[uid].append({"name": name, "price": price, "qty": 1})
            added.append(name.title())
    return added

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer_photo(
        "https://i.ibb.co/m9kJ7B/welcome-burger.png",
        caption=f"Здарова, {message.from_user.first_name}!\n\n*BURGER KING 2025 — НА МАКСИМАЛКАХ*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )

@dp.callback_query(lambda c: c.data == "menu")
async def show_menu(call: types.CallbackQuery):
    menu_text = "*МЕНЮ:*\n\n" + "\n".join([f"{name} — {price}₽" for name, price in current_menu.items()])
    await call.message.edit_caption(
        caption=menu_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Корзина", callback_data="cart")]])
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    await call.message.edit_caption(
        caption=get_cart_text(call.from_user.id),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Очистить", callback_data="clear")],
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
        await message.answer(f"Добавил: {', '.join(added)}!\n\n{get_cart_text(message.from_user.id)}")
        return

    # Если не заказ — спрашиваем у твоего AI
    ai_response = await ask_ai(message.text)
    await message.answer(ai_response)

async def main():
    print("БОТ ЗАПУЩЕН — САМЫЙ КРУТОЙ В РОССИИ!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
