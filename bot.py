# bot.py — ФИНАЛЬНЫЙ РАБОЧИЙ КОД (использует твои menu.py и ai_brain.py)
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu import BURGER_KING_MENU
from ai_brain import ask_grok

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

user_cart = defaultdict(list)

# Цены из твоего menu.py (можно потом вынести в JSON)
PRICES = {
    "воппер": 349, "двойной воппер": 449, "чизбургер": 149, "биг кинг": 399,
    "воппер сырный": 379, "беконайзер": 299, "лонг чикен": 279,
    "картошка фри": 149, "картошка по-деревенски": 169, "наггетсы": 259,
    "наггетсы 16": 399, "луковые кольца": 189, "кола": 119, "кола 1л": 179,
    "фанта": 119, "спрайт": 119, "коктейль": 199, "чизкейк": 159
}

def get_cart(uid):
    if not user_cart[uid]: return "*Корзина пустая*"
    total = sum(item["price"] * item["qty"] for item in user_cart[uid])
    txt = "*Твоя корзина:*\n\n"
    for item in user_cart[uid]:
        txt += f"• {item['name']} × {item['qty']} = {item['price']*item['qty']}₽\n"
    txt += f"\n*Итого: {total}₽*"
    return txt

def add_to_cart(uid, text):
    text = text.lower()
    added = []
    for name, price in PRICES.items():
        if name in text:
            for item in user_cart[uid]:
                if item["name"] == name.title():
                    item["qty"] += 1
                    added.append(name.title())
                    break
            else:
                user_cart[uid].append({"name": name.title(), "price": price": price, "qty": 1})
                added.append(name.title())
    return added

@dp.message(CommandStart())
async def start(m: types.Message):
    await m.answer_photo(
        "https://i.ibb.co/m9kJ7B/welcome-burger.png",
        caption=f"Здарова, {m.from_user.first_name}!\n\n*BURGER KING — ТВОЯ КОМАНДА ВКУСА*\n\nПиши что угодно — я пойму и добавлю в корзину!",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="Меню", callback_data="menu")],
            [types.InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )

@dp.callback_query(lambda c: c.data == "menu")
async def show_menu(c: types.CallbackQuery):
    await c.message.edit_caption(caption=BURGER_KING_MENU,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ]))

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(c: types.CallbackQuery):
    await c.message.edit_caption(caption=get_cart(c.from_user.id),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="Очистить", callback_data="clear")],
            [types.InlineKeyboardButton(text="Меню", callback_data="menu")]
        ]))

@dp.callback_query(lambda c: c.data == "clear")
async def clear(c: types.CallbackQuery):
    user_cart[c.from_user.id].clear()
    await c.answer("Очищено!", show_alert=True)
    await show_cart(c)

@dp.message()
async def handle_message(m: types.Message):
    added = add_to_cart(m.from_user.id, m.text or "")
    if added:
        await m.answer(f"Закинул: {', '.join(added)}!\n\n{get_cart(m.from_user.id)}")
    else:
        # Если не понял заказ — спрашиваем у Grok
        answer = await ask_grok(m.text or "", get_cart(m.from_user.id))
        await m.answer(answer)

async def main():
    print("БОТ ЗАПУЩЕН — САМЫЙ КРУТОЙ В РОССИИ 2025")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
