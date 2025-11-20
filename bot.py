# bot.py — ФИНАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ — 20 НОЯБРЯ 2025
import asyncio
import os
import logging
import httpx
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY")

# БЕЗ DefaultBotProperties — чтобы точно не падало
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_cart = defaultdict(list)

# Цены и синонимы
MENU_PRICES = {
    "воппер": 349, "двойной воппер": 449, "чизбургер": 149, "двойной чизбургер": 229,
    "биг кинг": 399, "картошка": 149, "наггетсы": 259, "кола": 119, "кола 1л": 179,
    "коктейль": 199, "соус": 49
}

BEAUTIFUL_MENU = """
*MENЮ BURGER KING — 2025*

*Бургеры*
Воппер — 349₽
Двойной Воппер — 449₽
Чизбургер — 149₽
Двойной Чизбургер — 229₽
Биг Кинг — 399₽

*Гарниры*
Картошка фри большая — 149₽
Наггетсы 9 шт — 259₽
Соус сырный — 49₽

*Напитки*
Кола 0.5л — 119₽
Кола 1л — 179₽
Молочный коктейль — 199₽

Пиши что угодно — я пойму!
"""

def get_cart(user_id):
    items = user_cart[user_id]
    if not items:
        return "*Корзина пустая*"
    total = sum(i["price"] * i["qty"] for i in items)
    text = "*Твоя корзина:*\n\n"
    for i in items:
        text += f"• {i['name'].title()} × {i['qty']} = {i['price']*i['qty']}₽\n"
    text += f"\n*Итого: {total}₽*"
    return text

async def ask_grok(text, cart):
    prompt = f"Меню: {BEAUTIFUL_MENU}\nКорзина: {cart}\nКлиент написал: {text}\nОтветь коротко и по-пацански"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post("https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROK_API_KEY}"},
                json={"model": "grok-2-latest", "messages": [{"role": "user", "content": prompt}], "temperature": 0.9},
                timeout=30)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
    except:
        pass
    return "Ща всё будет, брат"

def add_to_cart(user_id, text):
    text = text.lower()
    added = []
    for name, price in MENU_PRICES.items():
        if name in text:
            found = False
            for item in user_cart[user_id]:
                if item["name"] == name:
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
        caption=f"Здарова, {message.from_user.first_name}!\n\n"
                "*Burger King на максималках!*\n\n"
                "Пиши что хочешь — я всё пойму и добавлю в корзину сам!\n\n"
                "Пример:\n"
                "• Два воппера и колу\n"
                "• Картошку и наггетсы\n"
                "• Сколько с меня?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )

@dp.callback_query(lambda c: c.data == "menu")
async def menu(call: types.CallbackQuery):
    await call.message.edit_caption(
        caption=BEAUTIFUL_MENU,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "cart")
async def cart(call: types.CallbackQuery):
    await call.message.edit_caption(
        caption=get_cart(call.from_user.id),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Очистить", callback_data="clear")],
            [InlineKeyboardButton(text="Меню", callback_data="menu")]
        ])
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "clear")
async def clear(call: types.CallbackQuery):
    user_cart[call.from_user.id].clear()
    await call.answer("Корзина очищена!", show_alert=True)
    await cart(call)

@dp.message()
async def msg(message: types.Message):
    if not message.text:
        return

    added = add_to_cart(message.from_user.id, message.text)
    if added:
        await message.answer(f"Добавил: {', '.join(added)}\n\n{get_cart(message.from_user.id)}")
        return

    answer = await ask_grok(message.text, get_cart(message.from_user.id))
    await message.answer(answer)

async def main():
    logging.info("БОТ ЗАПУЩЕН — ГОТОВ К МИЛЛИОНАМ!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
